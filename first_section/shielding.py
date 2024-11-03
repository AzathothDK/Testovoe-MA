import re


class EmailShielding:
    def __init__(self, email: str, mask_ch: str = 'x'):
        self.email = email
        self.mask_ch = mask_ch

    def mask(self):
        local, domain = self.email.split('@')
        masked = self.mask_ch * len(local)
        return f"{masked}@{domain}"
    

class PhoneShielding:
    def __init__(self, phone: str, mask_char: str = 'x', mask_length: int = 3):
        self.phone = phone
        self.mask_char = mask_char
        self.mask_length = mask_length

    def mask(self):
        normalized_phone = re.sub(r'\s+', ' ', self.phone.strip())
        
        mask_section = self.mask_char * self.mask_length
        visible_section = normalized_phone[:-self.mask_length]
        
        return f"{visible_section}{mask_section}"


class SkypeShielding:
    def __init__(self, skype_id: str, mask_char: str = 'x'):
        self.skype_id = skype_id
        self.mask_char = mask_char

    def mask(self):
        skype_pattern = r"(skype:)([a-zA-Z0-9._]+)"
        return re.sub(skype_pattern, r"\1" + self.mask_char * 3, self.skype_id)
