import os


class Data(object):
    bread_types = ["White", "Seeds", "Walnut", "Walnut and Sultanas", "Pistacho",
                   "Wholemeal Spelt", "Wholemeal White", "Wholemeal Seeds", "Wholemeal Walnut",
                   "Wholemeal Nuts and Sultanas", "Wholemeal Pistachos"]
    invalid_characters = ["<", ">", "'", '"', "#", "%", "_", ";", "~"]
    tipos_pan = {"White_loaf": "Hogaza de Pan Blanco",
              "Seeds_loaf": "Hogaza de Pan de Semillas",
              "Walnut_loaf": "Hogaza de Pan de Nueces",
              "Walnut_and_Sultanas_loaf": "Hogaza de Nueces y Pasas",
              "Pistacho_loaf": "Hogaza de Pan de Pistachos",
              "Wholemeal_Spelt_loaf": "Hogaza de Pan Integral de Centeno>",
              "Wholemeal_White_loaf": "Hogaza de Pan Blanco Integral",
              "Wholemeal_Seeds_loaf": "Hogaza de Pan Integral de Semillas",
              "Wholemeal_Walnut_loaf": "Hogaza de Pan Integrales de Nueces",
              "Wholemeal_Walnut_and_Sultanas_loaf": "Hogaza de Pan Integral de Nueces y Pasas",
                
              "White_stick": "Barra de Pan Blanco",
              "Seeds_stick": "Barra de Pan de Semillas",
              "Walnut_stick": "Barra de Pan de Nueces",
              "Walnut_and_Sultanas_stick ": "Barra de Pan de Nueces y Pasas",
              "Pistacho_stick": "Barra de Pan de Pistachos",
              "Wholemeal_Spelt_stick": "Barra de Pan Integral de Espelta",
              "Wholemeal_White_stick": "Barra de Pan Blanco Integral",
              "Wholemeal_Seeds_stick": "Barra de Pan Blanco",
              "Wholemeal_Walnut_stick": "Barra de Pan Blanco",
              "Wholemeal_Walnut_and_Sultanas_stick": "Barra de Pan Blanco",}
    prices = {"White_loaf": 3,
              "Seeds_loaf": 3,
              "Walnut_loaf": 4,
              "Walnut_and_Sultanas_loaf": 4,
              "Pistacho_loaf": 4.5,
              "Wholemeal_Spelt_loaf": 4,
              "Wholemeal_White_loaf": 4,
              "Wholemeal_Seeds_loaf": 4,
              "Wholemeal_Walnut_loaf": 4,
              "Wholemeal_Walnut_and_Sultanas_loaf": 4,
              "White_stick": 2,
              "Seeds_stick": 2,
              "Walnut_stick": 2.5,
              "Walnut_and_Sultanas_stick ": 2.5,
              "Pistacho_stick": 3,
              "Wholemeal_Spelt_stick": 2.5,
              "Wholemeal_White_stick": 2.5,
              "Wholemeal_Seeds_stick": 2.5,
              "Wholemeal_Walnut_stick": 2.5,
              "Wholemeal_Walnut_and_Sultanas_stick": 2.5}
class SecretData(object):
    secret_key = os.getenv('SECRET_KEY_FlASK')


if __name__ == "__main__":
    data = SecretData()