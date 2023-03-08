import unittest
from unittest.mock import MagicMock, patch
from p2p_simulator import *
import re

class TestVirtualMachine(unittest.TestCase):
    def setUp(self):
        self.config = [1, ['2000', '2001', '2002'], 1]
        self.vm = VirtualMachine(self.config)

    def test_logical_clock_initialization(self):
        self.assertEqual(self.vm.clock.counter, 0)

    def test_logical_clock_update(self):
        self.vm.clock.update()
        self.assertEqual(self.vm.clock.counter, 1)
        
    def test_logical_clock_update2(self):
        self.vm.clock.update(5)
        self.assertEqual(self.vm.clock.counter, 6)
        
    def test_logical_clock_update3(self):
        self.vm.clock.update(-1)
        self.assertEqual(self.vm.clock.counter, 1)

    def test_log_data_initialization(self):
        log_data = LogData(1, 0, 'INTERNAL', 0, None, None, 4)
        self.assertEqual(log_data.id, 1)
        self.assertEqual(log_data.clock_counter, 0)
        self.assertEqual(log_data.event_type, 'INTERNAL')
        self.assertEqual(log_data.post_queue_length, 0)
        self.assertEqual(log_data.sender, None)
        self.assertEqual(log_data.reciever, None)
        self.assertEqual(log_data.description, 4)

    def test_log_data_get_log_string(self):
        log_data = LogData(1, 0, 'INTERNAL', 0, None, None, 4)
        log_string = log_data.get_log_string()
        value = re.match(r"1,\d+,0,INTERNAL,None,None,4,0", log_string)
        self.assertTrue(value)

    def test_virtual_machine_run(self):
        mock_init_machine = MagicMock()
        self.vm.init_machine = mock_init_machine
        mock_socket = MagicMock()
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock()
        mock_socket.connect = MagicMock()
        with patch('socket.socket', return_value=mock_socket):
            self.vm.run(1)
        mock_init_machine.assert_called_once()
        mock_socket.connect.assert_called()

if __name__ == '__main__':
    os.mkdir(f"logs/logs_1")
    with open('logs/logs_1/1.csv', 'w') as fp:
        pass
    unittest.main()