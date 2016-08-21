from MultiTorProxy import MultiTorProxy
import time

if __name__ == '__main__':
    multi_tor_proxy = MultiTorProxy()
    multi_tor_proxy.start()

    while True:
        time.sleep(60)