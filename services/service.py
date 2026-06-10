from fastapi import HTTPException


class Service:
    def handle_response(self, response: dict) -> dict:
        if not response.get("success"):
            raise HTTPException(
                status_code=response.get("code", 500),
                detail=response
            )
        return response

    def raise_exception(self, code : int, msg : str):
        raise HTTPException(
            status_code=code,
            detail=msg
        )
