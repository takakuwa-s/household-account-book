from src.app.functions.submit_reciepts import callback
from src.app.usecase.usecase import register_expenditure

def main(event, context):
    return callback(event, context)

if __name__ == "__main__":
    register_expenditure()