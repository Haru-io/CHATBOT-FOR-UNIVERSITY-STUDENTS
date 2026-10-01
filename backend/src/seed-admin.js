import 'dotenv/config';
import bcrypt from 'bcryptjs';
import crypto from 'crypto';
import { addUser, findUserByEmail } from './store.js';

const email=process.env.ADMIN_EMAIL||'admin@p200.local';
const password=process.env.ADMIN_PASSWORD||'Admin@12345';
const name=process.env.ADMIN_NAME||'P200 Admin';
if(await findUserByEmail(email)) { console.log('Admin already exists'); process.exit(0); }
await addUser({id:crypto.randomUUID(),name,email,passwordHash:await bcrypt.hash(password,12),role:'ADMIN',createdAt:new Date().toISOString()});
console.log(`Admin created: ${email} / ${password}`);
