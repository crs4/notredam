BROKER_URL = "amqp://guest:guest@156.148.22.12:5672//"
CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = ("dam.mprocessor.processor", 
                  "dam.mprocessor.servers.generic_cmd",
                  "dam.mprocessor.servers.xmp_embedder",
                  "dam.mprocessor.servers.xmp_extractor",)
