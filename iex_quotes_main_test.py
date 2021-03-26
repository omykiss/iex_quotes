import unittest
from unittest import mock
from iex_quotes_main import *

class TestIex(unittest.TestCase):

    def test_is_pos_digit_01(self):
        retval = is_pos_digit('-1')        
        self.assertEqual(retval, False)

    def test_is_pos_digit_02(self):        
        retval = is_pos_digit('1.1')
        self.assertEqual(retval, False)

    def test_is_pos_digit_03(self):        
        retval = is_pos_digit('a')
        self.assertEqual(retval, False)

    def test_is_pos_digit_04(self):
        retval = is_pos_digit('0')
        self.assertEqual(retval, True)

    def test_is_pos_digit_05(self):
        retval = is_pos_digit('1')
        self.assertEqual(retval, True)

    def test_is_pos_digit_06(self):
        retval = is_pos_digit('9999')
        self.assertEqual(retval, True)

    def test_exception_exit(self):
        with self.assertRaises(SystemExit) as cm:
            exception_exit('foo')

        self.assertEqual(cm.exception.code, 1)    

    def test_confirm_selection_01(self):
        retval = confirm_selection('Y')
        self.assertEqual(retval, True)

    def test_confirm_selection_02(self):        
        retval = confirm_selection('y')
        self.assertEqual(retval, True)

    def test_confirm_selection_03(self):
        retval = confirm_selection('N')
        self.assertEqual(retval, False)

    def test_confirm_selection_04(self):
        retval = confirm_selection('n')
        self.assertEqual(retval, False)

    def test_confirm_selection_05(self):
        retval = confirm_selection('')
        self.assertEqual(retval, False)

    def test_read_env_file_dev(self):
        dev_token = 'Tsk_32a0aad3142c42cbb9933f03b7a9ac21'
        dev_url = 'https://sandbox.iexapis.com/stable/stock/'
        dev = [dev_token, dev_url]
        
        tokens = read_env_file('env_file.csv')
        
        self.assertEqual(tokens['dev'], dev)        
    
    def test_read_env_file_prod(self):
        None        
        #prod_token = '<insert_prod_token>'
        #prod_url = 'https://cloud.iexapis.com/stable/stock/'
        #prod = [prod_token, prod_url]

        #tokens = read_env_file('env_file.csv')
        
        #self.assertEqual(tokens['prod'], prod)        

    @mock.patch('iex_quotes_main.input', create = True)
    def test_set_env_01(self, mocked_input):        
        in_token_url_1 = ['test_token_123','https://test_api_url.com']
        in_hash_map = {'dev' : in_token_url_1}
        mocked_input.side_effect = ['0', 'y']
        retval = set_env(in_hash_map)
        self.assertEqual(retval, in_token_url_1)

    @mock.patch('iex_quotes_main.input', create = True)
    def test_set_env_02(self, mocked_input):        
        in_token_url_1 = ['test_token_123','https://test_api_url.com']
        in_token_url_2 = ['test_token_456','https://test_api_url.org']
        in_hash_map = {'dev' : in_token_url_1}
        in_hash_map['test'] = in_token_url_2
        mocked_input.side_effect = ['1', 'y']
        retval = set_env(in_hash_map)
        self.assertEqual(retval, in_token_url_2)

    @mock.patch('iex_quotes_main.input', create = True)
    def test_set_env_03(self, mocked_input):  
        in_token_url_1 = ['test_token_123','https://test_api_url.com']
        in_hash_map = {'dev' : in_token_url_1}      
        # Selection confirmation is false
        mocked_input.side_effect = ['0', 'n']
        self.assertRaises(ValueError, set_env, in_hash_map)
    
    @mock.patch('iex_quotes_main.input', create = True)
    def test_set_env_04(self, mocked_input):  
        in_token_url_1 = ['test_token_123','https://test_api_url.com']
        in_hash_map = {'dev' : in_token_url_1}      
        # Envrionment selection out of range
        mocked_input.side_effect = ['2', 'y']        
        self.assertRaises(ValueError, set_env, in_hash_map)

    @mock.patch('iex_quotes_main.input', create = True)
    def test_set_env_05(self, mocked_input):  
        in_token_url_1 = ['test_token_123','https://test_api_url.com']
        in_hash_map = {'dev' : in_token_url_1}      
        # Envrionment selection not a number >= 0
        mocked_input.side_effect = ['a', 'y']        
        self.assertRaises(TypeError, set_env, in_hash_map)
    
if __name__ == '__main__':
    unittest.main()