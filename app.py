from flask import Flask, request
from flask_restful import Resource, Api
from flasgger import Swagger

app = Flask(__name__)
api = Api(app)
swagger = Swagger(app)

books = []
book_id_counter = 1

class BookListResource(Resource):
    def get(self):
        """
        Отримати список усіх книг
        ---
        responses:
          200:
            description: Успішний запит
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  title:
                    type: string
                  author:
                    type: string
        """
        return books, 200

    def post(self):
        """
        Додати нову книгу
        ---
        parameters:
          - in: body
            name: body
            schema:
              type: object
              required:
                - title
                - author
              properties:
                title:
                  type: string
                author:
                  type: string
        responses:
          201:
            description: Книгу успішно створено
        """
        global book_id_counter
        data = request.get_json()
        new_book = {
            "id": book_id_counter,
            "title": data.get("title"),
            "author": data.get("author")
        }
        books.append(new_book)
        book_id_counter += 1
        return new_book, 201

class BookResource(Resource):
    def get(self, book_id):
        """
        Отримати книгу за ідентифікатором
        ---
        parameters:
          - name: book_id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Книгу знайдено
          404:
            description: Книгу не знайдено
        """
        book = next((b for b in books if b["id"] == book_id), None)
        if book:
            return book, 200
        return {"message": "Not found"}, 404

    def put(self, book_id):
        """
        Оновити дані існуючої книги
        ---
        parameters:
          - name: book_id
            in: path
            type: integer
            required: true
          - in: body
            name: body
            schema:
              type: object
              properties:
                title:
                  type: string
                author:
                  type: string
        responses:
          200:
            description: Дані книги оновлено
          404:
            description: Книгу не знайдено
        """
        data = request.get_json()
        book = next((b for b in books if b["id"] == book_id), None)
        if book:
            book["title"] = data.get("title", book["title"])
            book["author"] = data.get("author", book["author"])
            return book, 200
        return {"message": "Not found"}, 404

    def delete(self, book_id):
        """
        Видалити книгу
        ---
        parameters:
          - name: book_id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Книгу видалено
          404:
            description: Книгу не знайдено
        """
        global books
        initial_len = len(books)
        books = [b for b in books if b["id"] != book_id]
        if len(books) < initial_len:
            return {"message": "Deleted"}, 200
        return {"message": "Not found"}, 404

api.add_resource(BookListResource, '/books')
api.add_resource(BookResource, '/books/<int:book_id>')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)