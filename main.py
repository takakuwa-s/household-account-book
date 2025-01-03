from src.app.functions.submit_reciepts import callback
from src.app.usecase.hundle_line_message_usecase import test


def main(event, context):
    return callback(event, context)


# if __name__ == "__main__":
#     test()
