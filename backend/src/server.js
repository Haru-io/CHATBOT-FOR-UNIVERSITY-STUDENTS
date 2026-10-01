import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import crypto from 'crypto';
import fs from 'fs/promises';
import path from 'path';
import multer from 'multer';
import { auth, requireAdmin } from './auth.js';
import { addFeedback, addMessage, addUser, createSession, findUserByEmail, listMessages, listSessions } from './store.js';

const app=express();
const PORT=process.env.PORT||5000;
const AI=process.env.AI_SERVICE_URL||'http://127.0.0.1:8000';
const CLIENT=process.env.CLIENT_URL||'http://localhost:5173';
const uploadDir=path.resolve(process.cwd(), process.env.UPLOAD_DIR||'../knowledge-base/documents');
await fs.mkdir(uploadDir,{recursive:true});

app.use(cors({origin:CLIENT})); app.use(express.json({limit:'1mb'})); app.use(morgan('dev'));
const storage=multer.diskStorage({destination:(req,file,cb)=>cb(null,uploadDir),filename:(req,file,cb)=>cb(null,`${Date.now()}-${file.originalname.replace(/[^a-zA-Z0-9._-]/g,'_')}`)});
const upload=multer({storage, limits:{fileSize:15*1024*1024}, fileFilter:(req,file,cb)=>{
  const ok=['.pdf','.txt','.md','.json'].includes(path.extname(file.originalname).toLowerCase()); cb(ok?null:new Error('Only PDF/TXT/MD/JSON files are allowed'),ok);
}});

function tokenFor(user){return jwt.sign({sub:user.id,role:user.role},process.env.JWT_SECRET,{expiresIn:'7d'});}

app.get('/api/health',(req,res)=>res.json({status:'ok',service:'backend'}));

app.post('/api/auth/register',async(req,res)=>{
  try{
    const {name,email,password}=req.body||{};
    if(!name||!email||!password) return res.status(400).json({message:'Name, email and password are required'});
    if(password.length<6) return res.status(400).json({message:'Password must be at least 6 characters'});
    if(await findUserByEmail(email)) return res.status(409).json({message:'Email already registered'});
    const user={id:crypto.randomUUID(),name,email:email.toLowerCase(),passwordHash:await bcrypt.hash(password,12),role:'STUDENT',createdAt:new Date().toISOString()};
    await addUser(user); return res.status(201).json({token:tokenFor(user),user:{id:user.id,name:user.name,email:user.email,role:user.role}});
  }catch(e){return res.status(500).json({message:e.message});}
});

app.post('/api/auth/login',async(req,res)=>{
  const {email,password}=req.body||{}; const user=await findUserByEmail(email||'');
  if(!user || !(await bcrypt.compare(password||'',user.passwordHash))) return res.status(401).json({message:'Invalid email or password'});
  res.json({token:tokenFor(user),user:{id:user.id,name:user.name,email:user.email,role:user.role}});
});

app.get('/api/me',auth,(req,res)=>res.json({user:req.user}));

app.post('/api/chat',auth,async(req,res)=>{
  try{
    const {message,sessionId}=req.body||{}; if(!message?.trim()) return res.status(400).json({message:'Message is required'});
    let sid=sessionId;
    if(!sid){const s=await createSession({id:crypto.randomUUID(),userId:req.user.id,title:message.slice(0,60),createdAt:new Date().toISOString()}); sid=s.id;}
    await addMessage({id:crypto.randomUUID(),sessionId:sid,sender:'user',text:message,createdAt:new Date().toISOString()});
    const r=await fetch(`${AI}/chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})});
    if(!r.ok) throw new Error(`AI service returned ${r.status}`);
    const ai=await r.json();
    const saved=await addMessage({id:crypto.randomUUID(),sessionId:sid,sender:'assistant',text:ai.answer,meta:{intent:ai.intent,confidence:ai.confidence,provider:ai.provider,sources:ai.sources},createdAt:new Date().toISOString()});
    res.json({sessionId:sid,message:saved,ai});
  }catch(e){res.status(502).json({message:'AI service unavailable',detail:e.message});}
});

app.get('/api/chats',auth,async(req,res)=>res.json({sessions:await listSessions(req.user.id)}));
app.get('/api/chats/:id',auth,async(req,res)=>res.json({messages:await listMessages(req.params.id)}));
app.post('/api/feedback',auth,async(req,res)=>{
  const {messageId,rating,comment=''}=req.body||{}; if(!messageId||!['helpful','not_helpful'].includes(rating)) return res.status(400).json({message:'Invalid feedback'});
  await addFeedback({id:crypto.randomUUID(),messageId,userId:req.user.id,rating,comment,createdAt:new Date().toISOString()}); res.status(201).json({ok:true});
});

app.post('/api/admin/documents',auth,requireAdmin,upload.single('file'),async(req,res)=>{
  if(!req.file) return res.status(400).json({message:'File required'});
  try{const r=await fetch(`${AI}/reindex`,{method:'POST'}); const data=await r.json(); res.status(201).json({file:req.file.originalname,reindex:data});}
  catch(e){res.status(201).json({file:req.file.originalname,reindex:'AI service unavailable; restart/reindex later'});}
});
app.get('/api/admin/documents',auth,requireAdmin,async(req,res)=>{
  const files=await fs.readdir(uploadDir,{withFileTypes:true}); res.json({files:files.filter(f=>f.isFile()).map(f=>f.name)});
});

app.use((err,req,res,next)=>res.status(500).json({message:err.message||'Server error'}));
app.listen(PORT,()=>console.log(`P_200 backend running on http://localhost:${PORT}`));
