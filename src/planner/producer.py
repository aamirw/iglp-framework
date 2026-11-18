class Producer:
    def __init__(
        self, id, name, trade, enterprise="", valueChainParameters=None
    ) -> None:
        self.id = id  # int
        self.name = name  # string
        self.trade = trade  # string
        self.enterprise = enterprise  # string
        self.valueChainParameters = valueChainParameters  # dict

    def __repr__(self) -> str:
        return f"""Producer(id={self.id}, 
                name='{self.name}', 
                trade='{self.trade}',
                enterprise='{self.enterprise}', 
                valueChainParameters={self.valueChainParameters})"""

    def getValueChainParameters(self) -> dict:
        return self.valueChainParameters

    def getAllAttributes(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "trade": self.trade,
            "enterprise": self.enterprise,
            "valueChainParameters": self.valueChainParameters,
        }
