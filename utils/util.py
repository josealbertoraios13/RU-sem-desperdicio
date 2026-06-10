class Util:
    @staticmethod
    def return_http_exception(message: str = "null") -> None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail={"msg": message})
