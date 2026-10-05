from threading import Thread


class BackgroundDispatcher:
    def submit(self, action):
        Thread(target=action, daemon=True, name="ace-candidate-worker").start()
