# P_200 Backend

Node.js + Express API for authentication, chat sessions, feedback and admin document upload.

The prototype persists data to `backend/data/store.json` so it can run without MongoDB. For the production version, replace the persistence layer with MongoDB/Mongoose using the `MONGO_URI` in `.env`.

## Run
```bash
npm install
copy .env.example .env
npm run dev
```
