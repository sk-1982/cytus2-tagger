class ExpansionPackInfo:
    def __init__(self, data):
        self.id: str = data['ExpansionPackId']
        self.name: str = data['ExpansionPackName']
        self.price = float(data['DefaultPrice'].strip('$') or 0)
        self.icon_id: str = data['IconPath']
        self.order: int = data['CreateOrder']

    def __str__(self):
        return f'ExpansionPackInfo(id={self.id}, name={self.name}, price={self.price})'

    __repr__ = __str__
