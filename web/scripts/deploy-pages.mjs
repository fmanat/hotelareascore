// Explicit owner-invoked deployment only. Never imported by build or CI.
import {execFileSync} from 'node:child_process';
import {readFileSync, existsSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const webRoot = fileURLToPath(new URL('..', import.meta.url));
const repoRoot = path.dirname(webRoot);
const wrangler = path.join(webRoot, 'node_modules/.bin/wrangler');
export function requireExistingProject(projects) {
  const project = projects.find(p => p['Project Name'] === 'staycontext');
  if (!project) throw new Error('Existing Pages project staycontext not found. Stop; never create a replacement.');
  if (!(project['Project Domains'] ?? '').split(',').map(s=>s.trim()).includes('staycontext.com')) throw new Error('Existing staycontext project does not list staycontext.com; stop for owner review.');
}
export function requirePrivateBuild(robots, sitemapExists) {
  if (!/^Disallow:\s*\/\s*$/m.test(robots) || /^Sitemap:/mi.test(robots) || sitemapExists) {
    throw new Error('Deployment requires indexing OFF and no exposed sitemap.');
  }
}
export function deploy(run, inspectBuild) {
  if (run('git',['branch','--show-current']).trim() !== 'main') throw new Error('Deploy only from main.');
  if (run('git',['status','--porcelain']).trim()) throw new Error('Commit and push all changes before deployment.');
  const head = run('git',['rev-parse','HEAD']).trim();
  if (head !== run('git',['rev-parse','origin/main']).trim()) throw new Error('HEAD must match origin/main.');
  // Read-only preflight; CI=true and closed stdin prohibit interactive login/create.
  requireExistingProject(JSON.parse(run(wrangler,['pages','project','list','--json'])));
  run('npm',['--prefix',webRoot,'run','build'],true);
  run('python3',[path.join(webRoot,'scripts/seo_assertions.py')],true,webRoot);
  inspectBuild();
  run(wrangler,['pages','deploy',path.join(webRoot,'dist'),'--project-name','staycontext','--branch','main','--commit-hash',head],true);
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const run = (command,args,stream=false,cwd=repoRoot) => execFileSync(command,args,{
    cwd, encoding:'utf8', env:{...process.env,CI:'true',WRANGLER_SEND_METRICS:'false'},
    stdio:stream ? ['ignore','inherit','inherit'] : ['ignore','pipe','inherit'],
  }) ?? '';
  deploy(run,() => requirePrivateBuild(readFileSync(path.join(webRoot,'dist/robots.txt'),'utf8'),
    ['sitemap.xml','sitemap-index.xml','sitemap-hotels.xml'].some(f=>existsSync(path.join(webRoot,'dist',f)))));
}
