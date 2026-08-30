class LinguisticNucleus:
    """
    Núcleo Linguístico da STAR.
    """

    name = "linguistic"

    def process(self, text, context=None):

        return {
            "type": "linguistic",
            "input": text,
            "context": context,
        }