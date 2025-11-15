"""
Bank class representing bank transactions tied to the game.
"""

import os
import json
import re
import webbrowser
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, List
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from intuitlib.client import AuthClient
from intuitlib.exceptions import AuthClientError
from intuitlib.enums import Scopes
from quickbooks import QuickBooks
from quickbooks.objects.account import Account
from quickbooks.objects.customer import Customer
from quickbooks.objects.invoice import Invoice
from quickbooks.objects.payment import Payment
from quickbooks.objects.bill import Bill
from bank_transaction import BankTransaction


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""
    
    def do_GET(self):
        """Handle OAuth callback GET request."""
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        if 'code' in query_params and 'realmId' in query_params:
            self.server.auth_code = query_params['code'][0]
            self.server.realm_id = query_params['realmId'][0]
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Authorization Successful</title></head>
                <body>
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the application.</p>
                </body>
                </html>
            """)
        else:
            # Send error response
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Authorization Failed</title></head>
                <body>
                    <h1>Authorization Failed</h1>
                    <p>Missing required parameters. Please try again.</p>
                </body>
                </html>
            """)
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class Bank:
    """
    A Bank manages real-world USD transactions tied to the game.
    
    Attributes:
        transactions: List of BankTransaction objects, sorted by date
    """
    
    def __init__(self, transactions_dir: Optional[str] = None):
        """
        Initialize a Bank and load transactions.
        
        Args:
            transactions_dir: Directory containing bank transaction JSON files
                            (defaults to BankTransaction.DATA_DIRECTORY)
        """
        if transactions_dir is None:
            transactions_dir = f"./{BankTransaction.DATA_DIRECTORY}"
        
        self.transactions: List[BankTransaction] = []
        self._load_transactions(transactions_dir)
    
    def _load_transactions(self, transactions_dir: str):
        """
        Load bank transactions from JSON files in the directory.
        
        Args:
            transactions_dir: Directory containing bank transaction JSON files
        """
        transactions_path = Path(transactions_dir)
        
        if not transactions_path.exists():
            # Transactions directory is optional - if it doesn't exist, just return
            return
        
        # Load all .txt JSON files
        for json_file in sorted(transactions_path.glob("*.txt")):
            try:
                transaction = BankTransaction(filename=str(json_file))
                self.transactions.append(transaction)
            except Exception as e:
                print(f"Warning: Failed to load bank transaction from {json_file}: {e}")
        
        # Sort by date
        self.transactions.sort(key=lambda t: (t.get_date_as_datetime() or datetime.min))
    
    def get_account_balance(self, account: str) -> float:
        """
        Calculate the total balance for a given account.
        
        Args:
            account: Account string identifier
            
        Returns:
            Total net USD balance (revenue - cost) for the account
        """
        balance = 0.0
        for transaction in self.transactions:
            if transaction.account == account:
                balance += transaction.net_usd()
        return balance
    
    def get_transactions_by_account(self, account: str) -> List[BankTransaction]:
        """
        Get all transactions for a given account.
        
        Args:
            account: Account string identifier
            
        Returns:
            List of BankTransaction objects for the account, sorted by date
        """
        return [t for t in self.transactions if t.account == account]
    
    def _save_tokens_to_env(self, realm_id: str, access_token: str, refresh_token: str, env_suffix: str = ''):
        """
        Save OAuth tokens to .env file.
        
        Args:
            realm_id: Company realm ID
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            env_suffix: Environment suffix ('_DEV' or '_PROD') to append to variable names
        """
        env_path = Path('.env')
        if not env_path.exists():
            print("Warning: .env file not found, cannot save tokens")
            return
        
        # Read current .env content
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Update or add tokens with environment suffix
        tokens_to_update = {
            f'INTUIT_REALM_ID{env_suffix}': realm_id,
            f'INTUIT_ACCESS_TOKEN{env_suffix}': access_token,
            f'INTUIT_REFRESH_TOKEN{env_suffix}': refresh_token,
        }
        
        for key, value in tokens_to_update.items():
            # Check if key exists (commented or not)
            pattern = rf'^#?\s*{re.escape(key)}=.*$'
            if re.search(pattern, content, re.MULTILINE):
                # Replace existing line
                content = re.sub(pattern, f'{key}={value}', content, flags=re.MULTILINE)
            else:
                # Add new line at the end
                if not content.endswith('\n'):
                    content += '\n'
                content += f'{key}={value}\n'
        
        # Write back to .env
        with open(env_path, 'w') as f:
            f.write(content)
        
        print(f"Saved tokens to .env file (environment: {env_suffix or 'default'})")
    
    def _launch_oauth_flow(self, auth_client: AuthClient, redirect_uri: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Launch OAuth flow and return (realm_id, access_token, refresh_token).
        
        Args:
            auth_client: Initialized AuthClient
            redirect_uri: The redirect URI registered in Intuit app settings
        
        Returns:
            Tuple of (realm_id, access_token, refresh_token) or (None, None, None) on failure
        """
        print("Launching OAuth flow...")
        
        # Check if using OAuth2 Playground (requires manual code entry)
        is_playground = 'OAuth2Playground' in redirect_uri
        
        if is_playground:
            print(f"Using OAuth2 Playground redirect URI: {redirect_uri}")
            print("After authorization, you'll need to copy the code and realmId from the page.\n")
        else:
            print(f"Starting local callback server on {redirect_uri}\n")
        
        # Parse redirect URI to get host and port (only for localhost)
        server = None
        server_thread = None
        if not is_playground:
            parsed = urlparse(redirect_uri)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 8000
            
            # Create HTTP server for OAuth callback
            server = HTTPServer((host, port), OAuthCallbackHandler)
            server.auth_code = None
            server.realm_id = None
            
            # Start server in a thread
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
        
        try:
            # Get authorization URL
            scopes = [Scopes.ACCOUNTING]
            auth_url = auth_client.get_authorization_url(scopes)
            
            print(f"Opening browser to authorization URL...")
            print(f"If browser doesn't open, visit: {auth_url}\n")
            
            # Open browser
            try:
                webbrowser.open(auth_url)
            except Exception as e:
                print(f"Could not open browser automatically: {e}")
                print(f"Please visit: {auth_url}\n")
            
            if is_playground:
                # For Playground, user needs to manually enter code and realm_id
                print("="*80)
                print("MANUAL CODE ENTRY REQUIRED")
                print("="*80)
                print("\nAfter authorizing, the OAuth2 Playground page will show:")
                print("  - An authorization 'code'")
                print("  - A 'realmId' (company ID)")
                print("\nPlease copy both values from the page and enter them below.\n")
                
                auth_code = input("Enter the authorization code: ").strip()
                realm_id = input("Enter the realmId: ").strip()
                
                if not auth_code or not realm_id:
                    print("Error: Both code and realmId are required")
                    return None, None, None
            else:
                # For localhost, wait for callback
                print("Waiting for authorization...")
                print("(This will timeout after 5 minutes)\n")
                
                # Wait for callback (with timeout)
                timeout = 300  # 5 minutes
                start_time = time.time()
                while server.auth_code is None:
                    if time.time() - start_time > timeout:
                        print("\nTimeout waiting for authorization")
                        if server:
                            server.shutdown()
                        return None, None, None
                    time.sleep(0.5)
                
                # Got the auth code
                auth_code = server.auth_code
                realm_id = server.realm_id
                
                print(f"Received authorization code")
                print(f"Realm ID: {realm_id}\n")
                
                # Shutdown server
                if server:
                    server.shutdown()
                if server_thread:
                    server_thread.join(timeout=5)
            
            # Exchange code for tokens
            print("Exchanging authorization code for tokens...")
            try:
                auth_client.get_bearer_token(auth_code, realm_id=realm_id)
                access_token = auth_client.access_token
                refresh_token = auth_client.refresh_token
                
                print("Successfully obtained tokens!\n")
                
                # Save tokens to .env (with environment suffix)
                env_mode = os.getenv('ENV', 'dev').lower()
                if env_mode not in ['dev', 'prod']:
                    env_mode = 'dev'
                env_suffix = '_DEV' if env_mode == 'dev' else '_PROD'
                self._save_tokens_to_env(realm_id, access_token, refresh_token, env_suffix)
                
                return realm_id, access_token, refresh_token
                
            except AuthClientError as e:
                print(f"Error exchanging code for tokens: {e}")
                return None, None, None
                
        except Exception as e:
            print(f"Error during OAuth flow: {e}")
            import traceback
            traceback.print_exc()
            if server:
                server.shutdown()
            return None, None, None
    
    def _fetch_all_with_pagination(self, obj_class, client: QuickBooks, max_results_per_page: int = 1000, query_filter: Optional[str] = None):
        """
        Fetch all records of a given type with pagination support.
        
        Args:
            obj_class: The QuickBooks object class (e.g., Invoice, Payment, etc.)
            client: QuickBooks client instance
            max_results_per_page: Maximum results per page (default 1000, max allowed by API)
            query_filter: Optional query filter string (e.g., "Status = 'Pending'")
        
        Returns:
            List of all records
        """
        all_records = []
        start_position = 1
        max_results = min(max_results_per_page, 1000)  # QuickBooks API max is 1000
        
        while True:
            try:
                # Use query if filter is provided, otherwise use all()
                if query_filter:
                    # Try using query method for filtered results
                    try:
                        page_records = obj_class.query(
                            query_filter,
                            qb=client,
                            start_position=start_position,
                            max_results=max_results
                        )
                    except Exception:
                        # If query fails, fall back to all()
                        page_records = obj_class.all(
                            qb=client,
                            start_position=start_position,
                            max_results=max_results
                        )
                else:
                    # Fetch a page of results
                    page_records = obj_class.all(
                        qb=client,
                        start_position=start_position,
                        max_results=max_results
                    )
                
                if not page_records:
                    break
                
                all_records.extend(page_records)
                
                # If we got fewer than max_results, we've reached the end
                if len(page_records) < max_results:
                    break
                
                # Move to next page
                start_position += len(page_records)
                
            except Exception as e:
                print(f"Error fetching page starting at {start_position}: {e}")
                break
        
        return all_records
    
    def _test_token_validity(self, auth_client: AuthClient, realm_id: str) -> bool:
        """Test if the current tokens are valid by making a test API call."""
        if not auth_client.access_token or not realm_id:
            return False
        
        try:
            # Try to create a QuickBooks client and make a simple API call
            client = QuickBooks(
                auth_client=auth_client,
                company_id=realm_id,
            )
            # Try to fetch company info (lightweight call)
            from quickbooks.objects.company_info import CompanyInfo
            CompanyInfo.get('1', qb=client)
            return True
        except Exception:
            # Token is invalid or expired
            return False
    
    def fetch_and_echo_intuit_data(self):
        """
        Fetch all account data from Intuit QuickBooks and echo it out.
        
        This method:
        1. Loads Intuit credentials from .env (respecting ENV=dev or ENV=prod)
        2. Authenticates with Intuit API (handles OAuth if needed)
        3. Fetches all available account data
        4. Echoes the data to stdout
        """
        # Load environment variables
        load_dotenv()
        
        # Determine which environment to use (dev or prod)
        env_mode = os.getenv('ENV', 'dev').lower()
        if env_mode not in ['dev', 'prod']:
            print(f"Warning: ENV must be 'dev' or 'prod', got '{env_mode}'. Defaulting to 'dev'.")
            env_mode = 'dev'
        
        env_suffix = '_DEV' if env_mode == 'dev' else '_PROD'
        print(f"\n{'='*80}")
        print(f"INTUIT QUICKBOOKS DATA FETCH - {env_mode.upper()} MODE")
        print(f"{'='*80}\n")
        
        # Load environment-specific credentials
        client_id = os.getenv(f'INTUIT_ID{env_suffix}')
        client_secret = os.getenv(f'INTUIT_SECRET{env_suffix}')
        app_id = os.getenv('INTUIT_APP_ID')  # App ID is shared between environments
        realm_id = os.getenv(f'INTUIT_REALM_ID{env_suffix}')  # Company ID
        access_token = os.getenv(f'INTUIT_ACCESS_TOKEN{env_suffix}')
        refresh_token = os.getenv(f'INTUIT_REFRESH_TOKEN{env_suffix}')
        environment = os.getenv(f'INTUIT_ENVIRONMENT{env_suffix}', 'sandbox' if env_mode == 'dev' else 'production')
        redirect_uri = os.getenv(f'INTUIT_REDIRECT_URI{env_suffix}')
        
        if not client_id or not client_secret:
            print(f"Error: INTUIT_ID{env_suffix} and INTUIT_SECRET{env_suffix} must be set in .env file")
            return
        
        if app_id:
            print(f"Using Intuit App ID: {app_id}")
        
        print(f"Environment: {env_mode.upper()} ({environment})")
        print(f"Client ID: {client_id[:10]}...")
        
        print("\n" + "="*80)
        print("FETCHING INTUIT QUICKBOOKS DATA")
        print("="*80 + "\n")
        
        try:
            # Get redirect URI from env or use default (OAuth2 Playground for development)
            if not redirect_uri:
                default_redirect_uri = 'https://developer.intuit.com/v2/OAuth2Playground/RedirectUrl'
                redirect_uri = default_redirect_uri
            
            # Initialize AuthClient
            auth_client = AuthClient(
                client_id=client_id,
                client_secret=client_secret,
                environment=environment,
                redirect_uri=redirect_uri,
            )
            
            # Check if we have tokens and if they're valid
            needs_oauth = False
            if access_token and refresh_token and realm_id:
                auth_client.access_token = access_token
                auth_client.refresh_token = refresh_token
                
                print("Found stored tokens. Testing validity...")
                if self._test_token_validity(auth_client, realm_id):
                    print("Stored tokens are valid!\n")
                else:
                    print("Stored tokens are invalid or expired. Attempting to refresh...")
                    try:
                        auth_client.refresh()
                        # Save refreshed tokens (with environment suffix)
                        self._save_tokens_to_env(realm_id, auth_client.access_token, auth_client.refresh_token, env_suffix)
                        print("Successfully refreshed tokens!\n")
                    except Exception as e:
                        print(f"Could not refresh tokens: {e}")
                        print("Need to complete OAuth flow again.\n")
                        needs_oauth = True
            else:
                print("No stored tokens found.\n")
                needs_oauth = True
            
            # Launch OAuth flow if needed
            if needs_oauth:
                # Use redirect URI already loaded (or default if not set)
                if not redirect_uri:
                    default_redirect_uri = 'https://developer.intuit.com/v2/OAuth2Playground/RedirectUrl'
                    redirect_uri = default_redirect_uri
                
                if redirect_uri == default_redirect_uri:
                    print(f"\n✓ Using Intuit OAuth2 Playground redirect URI (pre-configured):")
                    print(f"   {redirect_uri}")
                    print(f"   This URI is already registered in Intuit's system for development.\n")
                else:
                    print(f"\n⚠️  IMPORTANT: Make sure this redirect URI is registered in your Intuit app:")
                    print(f"   {redirect_uri}")
                    print(f"\n   To add it:")
                    print(f"   1. Go to https://developer.intuit.com/app/developer/dashboard")
                    print(f"   2. Select your app (DataInterface)")
                    print(f"   3. Go to the 'Keys' tab")
                    print(f"   4. Add '{redirect_uri}' to the 'Redirect URIs' section")
                    print(f"   5. Save and try again")
                    print(f"\n   Alternatively, you can use the OAuth2 Playground URI (pre-configured):")
                    print(f"   {default_redirect_uri}\n")
                
                realm_id, access_token, refresh_token = self._launch_oauth_flow(auth_client, redirect_uri)
                if not realm_id or not access_token:
                    print("OAuth flow failed. Cannot fetch data.")
                    return
                # Update auth_client with new tokens
                auth_client.access_token = access_token
                auth_client.refresh_token = refresh_token
            
            # Now we should have valid tokens
            if not realm_id:
                realm_id = os.getenv('INTUIT_REALM_ID')
            
            if realm_id and auth_client.access_token:
                print(f"Connecting to QuickBooks company (realm_id: {realm_id})...")
                
                # Initialize QuickBooks client
                client = QuickBooks(
                    auth_client=auth_client,
                    company_id=realm_id,
                )
                
                print("Successfully connected! Fetching ALL data from all time...\n")
                print("Note: This may take a while for large datasets due to pagination.\n")
                
                # Fetch and echo Accounts (typically not paginated heavily)
                print("="*80)
                print("ACCOUNTS (All Time)")
                print("="*80)
                try:
                    accounts = self._fetch_all_with_pagination(Account, client)
                    print(f"Found {len(accounts)} accounts:\n")
                    for account in accounts:
                        account_dict = account.to_dict()
                        print(json.dumps(account_dict, indent=2, default=str))
                        print("-" * 80)
                except Exception as e:
                    print(f"Error fetching accounts: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Fetch and echo Customers (all time)
                print("\n" + "="*80)
                print("CUSTOMERS (All Time)")
                print("="*80)
                try:
                    customers = self._fetch_all_with_pagination(Customer, client)
                    print(f"Found {len(customers)} customers:\n")
                    for customer in customers:
                        customer_dict = customer.to_dict()
                        print(json.dumps(customer_dict, indent=2, default=str))
                        print("-" * 80)
                except Exception as e:
                    print(f"Error fetching customers: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Fetch and echo Invoices (all time, all historical)
                print("\n" + "="*80)
                print("INVOICES (All Time - All Historical Transactions)")
                print("="*80)
                try:
                    invoices = self._fetch_all_with_pagination(Invoice, client)
                    print(f"Found {len(invoices)} invoices (all time):\n")
                    for invoice in invoices:
                        invoice_dict = invoice.to_dict()
                        print(json.dumps(invoice_dict, indent=2, default=str))
                        print("-" * 80)
                except Exception as e:
                    print(f"Error fetching invoices: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Fetch and echo Payments (all time, all historical)
                print("\n" + "="*80)
                print("PAYMENTS (All Time - All Historical Transactions)")
                print("="*80)
                try:
                    payments = self._fetch_all_with_pagination(Payment, client)
                    print(f"Found {len(payments)} payments (all time):\n")
                    for payment in payments:
                        payment_dict = payment.to_dict()
                        print(json.dumps(payment_dict, indent=2, default=str))
                        print("-" * 80)
                except Exception as e:
                    print(f"Error fetching payments: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Fetch and echo Bills (all time, all historical)
                print("\n" + "="*80)
                print("BILLS (All Time - All Historical Transactions)")
                print("="*80)
                try:
                    bills = self._fetch_all_with_pagination(Bill, client)
                    print(f"Found {len(bills)} bills (all time):\n")
                    for bill in bills:
                        bill_dict = bill.to_dict()
                        print(json.dumps(bill_dict, indent=2, default=str))
                        print("-" * 80)
                except Exception as e:
                    print(f"Error fetching bills: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Fetch additional transaction types
                print("\n" + "="*80)
                print("ADDITIONAL TRANSACTION TYPES (All Time - Posted and Pending)")
                print("="*80)
                
                # Try to fetch other transaction types
                try:
                    from quickbooks.objects import SalesReceipt, CreditMemo, VendorCredit, JournalEntry, Deposit, Transfer, Purchase, PurchaseOrder
                    # Try to import BankTransaction (newer type for bank feed transactions)
                    try:
                        from quickbooks.objects.bank_transaction import BankTransaction as QBBankTransaction
                    except ImportError:
                        try:
                            from quickbooks.objects import BankTransaction as QBBankTransaction
                        except ImportError:
                            QBBankTransaction = None
                except ImportError:
                    # Some transaction types may not be available in all versions
                    print("Note: Some additional transaction types may not be available.")
                    SalesReceipt = CreditMemo = VendorCredit = JournalEntry = Deposit = Transfer = Purchase = PurchaseOrder = QBBankTransaction = None
                
                transaction_types = []
                if SalesReceipt:
                    transaction_types.append(('Sales Receipts', SalesReceipt, None))
                if CreditMemo:
                    transaction_types.append(('Credit Memos', CreditMemo, None))
                if VendorCredit:
                    transaction_types.append(('Vendor Credits', VendorCredit, None))
                if JournalEntry:
                    transaction_types.append(('Journal Entries', JournalEntry, None))
                if Deposit:
                    transaction_types.append(('Deposits', Deposit, None))
                if Transfer:
                    # Transfers - fetch all (both posted and pending)
                    transaction_types.append(('Transfers (All - Posted & Pending)', Transfer, None))
                if Purchase:
                    # Purchase transactions - important for expense tracking
                    transaction_types.append(('Purchases (All Time - Posted & Pending)', Purchase, None))
                if PurchaseOrder:
                    # Purchase Orders - pending purchases
                    transaction_types.append(('Purchase Orders (Pending Purchases)', PurchaseOrder, None))
                if QBBankTransaction:
                    # BankTransaction - newer type for bank feed transactions (includes pending)
                    transaction_types.append(('Bank Transactions (All - Posted & Pending)', QBBankTransaction, None))
                
                for type_name, obj_class, query_filter in transaction_types:
                    try:
                        print(f"\n{type_name}:")
                        transactions = self._fetch_all_with_pagination(obj_class, client, query_filter=query_filter)
                        print(f"  Found {len(transactions)} {type_name.lower()} (all time, including pending):\n")
                        for transaction in transactions:
                            transaction_dict = transaction.to_dict()
                            # Check if transaction has status field and indicate if pending
                            status = transaction_dict.get('Status', '')
                            if status:
                                print(f"  Status: {status}")
                            print(json.dumps(transaction_dict, indent=2, default=str))
                            print("-" * 80)
                    except Exception as e:
                        print(f"  Error fetching {type_name.lower()}: {e}")
                        # Don't print full traceback for optional transaction types
                
                # Try to fetch pending/unreconciled transactions using query
                print("\n" + "="*80)
                print("ATTEMPTING TO FETCH PENDING/UNRECONCILED TRANSACTIONS")
                print("="*80)
                print("\nNote: QuickBooks API may not directly expose pending status.")
                print("Fetching all transfers and transactions regardless of status...\n")
                
                # Try to query for transactions that might be pending
                # Note: This is experimental as QBO API doesn't always expose pending status
                try:
                    if Transfer:
                        print("Fetching all Transfers (including any pending):")
                        all_transfers = self._fetch_all_with_pagination(Transfer, client)
                        print(f"  Total transfers found: {len(all_transfers)}")
                        # Check each transfer for any status indicators
                        pending_count = 0
                        for transfer in all_transfers:
                            transfer_dict = transfer.to_dict()
                            # Look for any indicators of pending status
                            # (QBO may not expose this directly, but we'll check all fields)
                            if any(key.lower() in ['pending', 'unreconciled', 'status'] for key in transfer_dict.keys()):
                                print(f"  Transfer ID {transfer_dict.get('Id', 'unknown')} may have status info:")
                                print(json.dumps(transfer_dict, indent=2, default=str))
                                print("-" * 80)
                except Exception as e:
                    print(f"  Note: Could not fetch additional pending transaction info: {e}")
                    print("  (This is expected - QBO API may not expose pending status directly)")
                
            else:
                print("Cannot fetch data without realm_id and access tokens.")
            
        except Exception as e:
            print(f"Error connecting to Intuit: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*80)
        print("END OF INTUIT DATA FETCH")
        print("="*80 + "\n")
    
    def __repr__(self):
        return (
            f"Bank(transactions={len(self.transactions)}, "
            f"unique_accounts={len(set(t.account for t in self.transactions))})"
        )

