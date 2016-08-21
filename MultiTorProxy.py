import socket
import threading
import random
import tempfile
import os
import subprocess


class MultiTorProxy:
    def __init__(self, listen_port=53000, listen_address='localhost', max_connections=10, tor_instaces=7,
                 tor_start_port=54000, recv_buffer_size=4096):
        self.listen_port = listen_port
        self.listen_address = listen_address
        self.max_connections = max_connections
        self.recv_buffer_size = recv_buffer_size

        self.tor_instaces = tor_instaces
        self.tor_start_port = tor_start_port
        self.tor_ports = []

        self.temp_directory = tempfile.TemporaryDirectory()
        os.chmod(self.temp_directory.name, 0o700)

        self.tor_settings = {"SocksListenAddress": '127.0.0.1', "CookieAuthentication": '0'}

    def __del__(self):
        self.temp_directory.cleanup()

    def start(self):
        self._start_tor_instances()
        threading.Thread(target=self._main_loop).start()

    def update_tor_settings(self, tor_settings):
        self.tor_settings.update(tor_settings)

    def _start_tor_instances(self):
        for i in range(0, self.tor_instaces):
            threading.Thread(target=self._start_tor_instance, args=(i,)).start()

    def _start_tor_instance(self, instance_number):
        instance_data_directory = os.path.join(self.temp_directory.name, str(instance_number))
        if not os.path.exists(instance_data_directory):
            os.makedirs(instance_data_directory)
        os.chmod(instance_data_directory, 0o700)

        tor_instance_settings = self.tor_settings.copy()

        tor_instance_settings.update({"DataDirectory": instance_data_directory,
                                      "SocksPort": self.tor_start_port + instance_number})

        self.tor_ports.append(tor_instance_settings["SocksPort"])

        tor_settongs_file_path = os.path.join(instance_data_directory, 'tor_settings')

        with open(tor_settongs_file_path, "w") as file:
            for key in tor_instance_settings:
                file.write("%s %s\n" % (key, str(tor_instance_settings[key])))

        os.chmod(tor_settongs_file_path, 0o600)

        while True:
            try:
                subprocess.call(["tor", "-f", tor_settongs_file_path])
            except:
                pass

    def _main_loop(self):
        try:
            dock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dock_socket.bind((self.listen_address, self.listen_port))
            dock_socket.listen(self.max_connections)
            while True:
                self._on_accept(dock_socket.accept()[0])
        finally:
            threading.Thread(target=self._main_loop).start()

    def _forward(self, source, destination):
        while True:
            try:
                data = source.recv(self.recv_buffer_size)
            except Exception:
                self._on_close(source, destination)
                break

            if data:
                try:
                    destination.sendall(data)
                except Exception:
                    self._on_close(source, destination)
                    break
            else:
                self._on_close(source, destination)
                break

    def _on_accept(self, client_socket):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        tor_port = random.choice(self.tor_ports)
        server_socket.connect(('localhost', tor_port))

        threading.Thread(target=self._forward, args=(client_socket, server_socket)).start()
        threading.Thread(target=self._forward, args=(server_socket, client_socket)).start()

    def _on_close(self, source, destination):
        try:
            source.shutdown(socket.SHUT_RD)
        except Exception:
            pass

        try:
            destination.shutdown(socket.SHUT_WR)
        except Exception:
            pass