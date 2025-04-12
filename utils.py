import falcon


def error_response(resp: falcon.Response, status_code: str, message: str):
    resp.status = status_code
    resp.media = {"error": message}
