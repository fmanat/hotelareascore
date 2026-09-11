import test from 'node:test';
import assert from 'node:assert/strict';
import {deploy,requireExistingProject,requirePrivateBuild} from './deploy-pages.mjs';
test('missing project or wrong custom domain never creates a replacement',()=>{
  assert.throws(()=>requireExistingProject([]));
  assert.throws(()=>requireExistingProject([{'Project Name':'staycontext','Project Domains':'other.pages.dev'}]));
  requireExistingProject([{'Project Name':'staycontext','Project Domains':'staycontext.pages.dev, staycontext.com, www.staycontext.com'}]);
});
test('public sitemap or crawlable build aborts',()=>{
  assert.throws(()=>requirePrivateBuild('User-agent: *\nAllow: /',false));
  assert.throws(()=>requirePrivateBuild('Disallow: /',true));
  requirePrivateBuild('User-agent: *\nDisallow: /\n',false);
});
test('failed build cannot reach upload; successful path targets only existing project',()=>{
  for (const fail of [true,false]) {
    const calls=[];
    const run=(command,args)=>{
      calls.push([command,args]);
      if(command==='git')return args[0]==='branch'?'main':args[0]==='status'?'':'abc';
      if(args.includes('list'))return JSON.stringify([{'Project Name':'staycontext','Project Domains':'staycontext.pages.dev, staycontext.com, www.staycontext.com'}]);
      if(command==='npm'&&fail)throw Error('build failed');
      return '';
    };
    if(fail)assert.throws(()=>deploy(run,()=>{}));else deploy(run,()=>{});
    const uploads=calls.filter(([,args])=>args[0]==='pages'&&args[1]==='deploy');
    assert.equal(uploads.length,fail?0:1);
    if(!fail)assert.deepEqual(uploads[0][1].slice(3),['--project-name','staycontext','--branch','main','--commit-hash','abc']);
    assert.ok(calls.every(([,args])=>!args.includes('create')&&!args.includes('login')));
  }
});
