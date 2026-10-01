import jwt from 'jsonwebtoken';
import { findUserById } from './store.js';

export async function auth(req,res,next){
  const token=(req.headers.authorization||'').replace(/^Bearer\s+/,'');
  if(!token) return res.status(401).json({message:'Authentication required'});
  try{
    const payload=jwt.verify(token, process.env.JWT_SECRET);
    const user=await findUserById(payload.sub);
    if(!user) return res.status(401).json({message:'User not found'});
    req.user={id:user.id,name:user.name,email:user.email,role:user.role};
    next();
  }catch(e){
  console.log('JWT VERIFY ERROR:', e.message);
  return res.status(401).json({message:'Invalid or expired token'});
}
}
export function requireAdmin(req,res,next){ if(req.user?.role!=='ADMIN') return res.status(403).json({message:'Admin access required'}); next(); }
