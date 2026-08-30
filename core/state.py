class StarState:
    """
    Estado interno computacional da STAR.
    """

    def __init__(self):
        self.energy = 100
        self.attention = 100
        self.focus = 100
        self.curiosity = 50
        self.confidence = 80
        self.cognitive_load = 0

    def get_state(self):
        return {
            "energy": self.energy,
            "attention": self.attention,
            "focus": self.focus,
            "curiosity": self.curiosity,
            "confidence": self.confidence,
            "cognitive_load": self.cognitive_load,
        }

    def update(self, **values):
        for key, value in values.items():

            if hasattr(self, key):
                setattr(self, key, value)