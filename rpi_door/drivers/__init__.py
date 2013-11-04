from time import sleep


class AbstractDoor():

    check_for_codes = True

    def __init__(self, *args, **kwargs):
        # set GPIO pins to defaults
        # door - HIGH
        # red LED - HIGH
        self.lock()
        self.toggle_red_led(on=True)

    def main_loop(self):
        while True:
            data = self.get_key_code()
            if data and self.check_key_code(data):
                self.toggle_red_led()
                self.toggle_green_led(on=True)
                sleep(1)
                self.unlock()
                self.toggle_red_led(on=True)
                self.toggle_green_led()
            self.check_lock_request()

    def check_key_code(self, data):
        raise NotImplementedError("Not implemented.")

    def get_key_code(self):
        if self.check_for_codes:
            return self._read_RFID()
        return None

    def check_lock_request(self):
        raise NotImplementedError("Not implemented.")

    def _read_RFID(self):
        raise NotImplementedError("Not implemented.")

    def unlock(self):
        self.check_for_codes = False

    def lock(self):
        self.check_for_codes = True

    def toggle_red_led(self, on=False):
        raise NotImplementedError("Not implemented.")

    def toggle_green_led(self, on=False):
        raise NotImplementedError("Not implemented.")
