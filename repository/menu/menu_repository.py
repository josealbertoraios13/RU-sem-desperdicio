from repository.repository import Repository
from utils import logger


class MenuRepository(Repository):
    PART = "menu_repository"
    _menus_table_ensured = False

    def _ensure_menus_table(self) -> None:
        if MenuRepository._menus_table_ensured:
            return

        create_table_query = """
            CREATE TABLE IF NOT EXISTS menus (
                id BIGSERIAL PRIMARY KEY,
                image_url VARCHAR(500) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                lunch_image_url VARCHAR(500),
                lunch_filename VARCHAR(255),
                dinner_image_url VARCHAR(500),
                dinner_filename VARCHAR(255),
                uploaded_by BIGINT,
                uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
            );
            ALTER TABLE menus ADD COLUMN IF NOT EXISTS lunch_image_url VARCHAR(500);
            ALTER TABLE menus ADD COLUMN IF NOT EXISTS lunch_filename VARCHAR(255);
            ALTER TABLE menus ADD COLUMN IF NOT EXISTS dinner_image_url VARCHAR(500);
            ALTER TABLE menus ADD COLUMN IF NOT EXISTS dinner_filename VARCHAR(255);
            UPDATE menus
            SET lunch_image_url = COALESCE(lunch_image_url, image_url),
                lunch_filename = COALESCE(lunch_filename, filename)
            WHERE lunch_image_url IS NULL OR lunch_filename IS NULL;
            CREATE INDEX IF NOT EXISTS idx_menus_uploaded_at ON menus(uploaded_at DESC);
        """
        with self.get_connect() as conn, conn.cursor() as cursor:
            cursor.execute(create_table_query)
        MenuRepository._menus_table_ensured = True

    @staticmethod
    def _menu_columns() -> str:
        return """
            id,
            image_url,
            filename,
            lunch_image_url,
            lunch_filename,
            dinner_image_url,
            dinner_filename,
            uploaded_at,
            uploaded_by
        """

    def save_menu(
        self,
        image_url: str | None = None,
        filename: str | None = None,
        uploaded_by: int | None = None,
        lunch_image_url: str | None = None,
        lunch_filename: str | None = None,
        dinner_image_url: str | None = None,
        dinner_filename: str | None = None,
    ) -> dict:
        try:
            self._ensure_menus_table()
            lunch_image_url = lunch_image_url or image_url
            lunch_filename = lunch_filename or filename
            image_url = image_url or lunch_image_url
            filename = filename or lunch_filename

            if not image_url or not filename or not lunch_image_url or not lunch_filename:
                return self.build_response(
                    router="save_menu",
                    msg="Imagem do almoco e obrigatoria",
                    success=False,
                    code=400,
                )

            with self.get_connect() as conn, conn.cursor() as cursor:
                sql_query = """
                    INSERT INTO menus (
                        image_url,
                        filename,
                        lunch_image_url,
                        lunch_filename,
                        dinner_image_url,
                        dinner_filename,
                        uploaded_by
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING
                        id,
                        image_url,
                        filename,
                        lunch_image_url,
                        lunch_filename,
                        dinner_image_url,
                        dinner_filename,
                        uploaded_at,
                        uploaded_by
                """
                cursor.execute(
                    sql_query,
                    (
                        image_url,
                        filename,
                        lunch_image_url,
                        lunch_filename,
                        dinner_image_url,
                        dinner_filename,
                        uploaded_by,
                    ),
                )
                result = cursor.fetchone()

                if result:
                    columns = [desc[0] for desc in cursor.description]
                    data = dict(zip(columns, result))
                    return self.build_response(
                        router="save_menu",
                        msg="Cardápio salvo com sucesso!",
                        data=data,
                    )

                return self.build_response(
                    router="save_menu",
                    msg="Erro ao salvar cardápio",
                    success=False,
                    code=500,
                )

        except Exception as exception:
            logger.error(f"Error in save_menu: {exception}")
            return self.build_response(
                router="save_menu",
                msg="Erro interno do servidor",
                success=False,
                code=500,
            )

    def get_current_menu(self) -> dict:
        try:
            self._ensure_menus_table()
            with self.get_connect() as conn, conn.cursor() as cursor:
                sql_query = """
                    SELECT
                        id,
                        image_url,
                        filename,
                        lunch_image_url,
                        lunch_filename,
                        dinner_image_url,
                        dinner_filename,
                        uploaded_at,
                        uploaded_by
                    FROM menus
                    ORDER BY uploaded_at DESC
                    LIMIT 1
                """
                cursor.execute(sql_query)
                result = cursor.fetchone()

                if result:
                    columns = [desc[0] for desc in cursor.description]
                    data = dict(zip(columns, result))
                    return self.build_response(
                        router="get_current_menu",
                        msg="Cardápio encontrado com sucesso",
                        data=data,
                    )

                return self.build_response(
                    router="get_current_menu",
                    msg="Nenhum cardápio encontrado",
                    success=False,
                    code=404,
                )

        except Exception as exception:
            logger.error(f"Error in get_current_menu: {exception}")
            return self.build_response(
                router="get_current_menu",
                msg="Erro interno do servidor",
                success=False,
                code=500,
            )

    def get_menu_by_id(self, menu_id: int) -> dict:
        try:
            self._ensure_menus_table()
            with self.get_connect() as conn, conn.cursor() as cursor:
                sql_query = """
                    SELECT
                        id,
                        image_url,
                        filename,
                        lunch_image_url,
                        lunch_filename,
                        dinner_image_url,
                        dinner_filename,
                        uploaded_at,
                        uploaded_by
                    FROM menus
                    WHERE id = %s
                """
                cursor.execute(sql_query, (menu_id,))
                result = cursor.fetchone()

                if result:
                    columns = [desc[0] for desc in cursor.description]
                    data = dict(zip(columns, result))
                    return self.build_response(
                        router="get_menu_by_id",
                        msg="Cardápio encontrado com sucesso",
                        data=data,
                    )

                return self.build_response(
                    router="get_menu_by_id",
                    msg="Cardápio não encontrado",
                    success=False,
                    code=404,
                )

        except Exception as exception:
            logger.error(f"Error in get_menu_by_id: {exception}")
            return self.build_response(
                router="get_menu_by_id",
                msg="Erro interno do servidor",
                success=False,
                code=500,
            )
