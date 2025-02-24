class Config:
    DEBUG = True
    SWAGGER_URL = "/swagger"
    API_URL = "/static/swagger.json"

models = ["deepseek-r1-distill-llama-70b", "llama-3.3-70b-versatile", "gemma2-9b-it", "deepseek-r1-distill-qwen-32b"]
default_model = models[0]