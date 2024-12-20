from pftpyclient.basic_utilities import settings as gvst
import getpass
from pftpyclient.basic_utilities.settings import *
from cryptography.fernet import InvalidToken
from loguru import logger

CREDENTIAL_FILENAME = "manyasone_cred_list.txt"

class CredentialManager:
    def __init__(self,username,password):
        self.postfiat_username = username.lower()
        self.wallet_address_name = f'{self.postfiat_username}__v1xrpaddress'
        self.wallet_secret_name = f'{self.postfiat_username}__v1xrpsecret'
        self.google_doc_name = f'{self.postfiat_username}__googledoc'
        # self.key_variables = [self.wallet_address_name, self.wallet_secret_name, 'postfiatusername']
        self.key_variables = [self.wallet_address_name, self.wallet_secret_name, self.google_doc_name]
        self.pw_initiator = password
        self.credential_file_path = get_credential_file_path()

        try:
            self.pw_map = self.decrypt_creds(pw_decryptor=self.pw_initiator)
        except InvalidToken:
            raise ValueError("Invalid username or password")

        self.fields_that_need_definition = [i for i in self.key_variables if i not in self.pw_map.keys()]

    def decrypt_creds(self, pw_decryptor):
        '''Decrypts all credentials in the file'''
        encrypted_cred_map = _get_cred_map()

        decrypted_cred_map = {
            self.wallet_address_name: pwl.password_decrypt(token=encrypted_cred_map[self.wallet_address_name], password=pw_decryptor).decode('utf-8'),
            self.wallet_secret_name: pwl.password_decrypt(token=encrypted_cred_map[self.wallet_secret_name], password=pw_decryptor).decode('utf-8'),
            self.google_doc_name: pwl.password_decrypt(token=encrypted_cred_map[self.google_doc_name], password=pw_decryptor).decode('utf-8')
        }
        
        return decrypted_cred_map 
    
def _read_creds(credential_file_path):
    with open(credential_file_path, 'r') as f:
        credblock = f.read()
    return credblock

def _convert_credential_string_to_map(stringx):
    '''Converts a credential string to a map'''
    def convert_string_to_bytes(string):
        if string.startswith("b'"):
            return bytes(string[2:-1], 'utf-8')
        else:
            return string
    
    variables = re.findall(r'variable___\w+', stringx)
    map_constructor = {}
    
    for variable_to_work in variables:
        raw_text = stringx.split(variable_to_work)[1].split('variable___')[0].strip()
        variable_name = variable_to_work.split('variable___')[1]
        map_constructor[variable_name] = convert_string_to_bytes(string=raw_text)
    
    return map_constructor
    
def _get_cred_map():
    credblock = _read_creds(get_credential_file_path())
    return _convert_credential_string_to_map(credblock)   
    
def enter_and_encrypt_credential(credentials_dict, pw_encryptor):
    """
    Encrypt and store multiple credentials.

    :param credentials_dict: Dictionary of credential references and their values
    :param pw_encryptor: Password used for encryption
    """
    
    existing_cred_map = _get_cred_map()
    new_credentials = []
    
    for credential_ref, pw_data in credentials_dict.items():
        if credential_ref in existing_cred_map.keys():
            logger.error(f'Credential {credential_ref} is already loaded')
            return
        
        credential_byte_str = pwl.password_encrypt(message=bytes(pw_data, 'utf-8'), password=pw_encryptor)
        
        new_credentials.append(f'\nvariable___{credential_ref}\n{credential_byte_str}')
    
    if new_credentials:
        with open(get_credential_file_path(), 'a') as f:
            f.write(''.join(new_credentials))
        
        logger.debug(f"Added {len(new_credentials)} new credentials to {get_credential_file_path()}")
    else:
        logger.debug("No new credentials to add")

def cache_credentials(input_map):
    """
    Cache user credentials locally.
    
    :param input_map: Dictionary containing user credentials
    :return: String message indicating the result of the operation
    """
    try: 
        credentials = {
            f'{input_map["Username_Input"]}__v1xrpaddress': input_map['XRP Address_Input'],
            f'{input_map["Username_Input"]}__v1xrpsecret': input_map['XRP Secret_Input'],
            f'{input_map["Username_Input"]}__googledoc': input_map['Google Doc Share Link_Input']                
        }

        enter_and_encrypt_credential(
            credentials_dict=credentials,
            pw_encryptor=input_map['Password_Input']
        )

        return f'Information Cached and Encrypted Locally Using Password to {get_credential_file_path()}'
    
    except Exception as e:
        logger.error(f"Error caching credentials: {e}")
        return f"Error caching credentials: {e}"

def get_credentials_directory():
    '''Returns the path to the postfiatcreds directory, creating it if it does not exist'''
    creds_dir = Path.home().joinpath("postfiatcreds")
    creds_dir.mkdir(exist_ok=True)
    return creds_dir

def get_credential_file_path():
    '''Returns the path to the credential file, creating it if it does not exist'''
    creds_dir = get_credentials_directory()
    cred_file_path = creds_dir / CREDENTIAL_FILENAME
    
    if not cred_file_path.exists():
        cred_file_path.touch()
        logger.info(f"Created credentials file at {cred_file_path}")
    
    return cred_file_path

