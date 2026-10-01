import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const file = path.resolve(__dirname, '../data/store.json');

const empty = { users: [], sessions: [], messages: [], feedback: [] };

async function read() {
  try { return JSON.parse(await fs.readFile(file, 'utf8')); }
  catch { await write(empty); return structuredClone(empty); }
}
async function write(data) { await fs.mkdir(path.dirname(file), { recursive: true }); await fs.writeFile(file, JSON.stringify(data, null, 2)); }

export async function addUser(user) { const db=await read(); db.users.push(user); await write(db); return user; }
export async function findUserByEmail(email) { const db=await read(); return db.users.find(u=>u.email.toLowerCase()===email.toLowerCase()) || null; }
export async function findUserById(id) { const db=await read(); return db.users.find(u=>u.id===id) || null; }
export async function createSession(session) { const db=await read(); db.sessions.push(session); await write(db); return session; }
export async function listSessions(userId) { const db=await read(); return db.sessions.filter(s=>s.userId===userId).sort((a,b)=>new Date(b.createdAt)-new Date(a.createdAt)); }
export async function addMessage(message) { const db=await read(); db.messages.push(message); await write(db); return message; }
export async function listMessages(sessionId) { const db=await read(); return db.messages.filter(m=>m.sessionId===sessionId).sort((a,b)=>new Date(a.createdAt)-new Date(b.createdAt)); }
export async function addFeedback(item) { const db=await read(); db.feedback.push(item); await write(db); return item; }
