const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const TASKS_KEY = 'minimax-h3-history';
const USERS_KEY = 'minimax-h3-users';
const SESSION_KEY = 'minimax-h3-session';
const GENERATION_COST = 10;
const examples = ['清晨的海边，一列白色火车沿着悬崖缓慢驶过，阳光从云层间洒下', '雨夜的东京街头，透明雨伞在人群中穿行，霓虹倒映在湿漉漉的路面', '一只纸飞机掠过安静的书房，窗帘被风吹起，尘埃在光束里旋转'];
const intents = [
  {name:'自然叙事', chip:'航拍 · 宁静', keys:['海','山','森林','湖','天空','日出','悬崖','风']},
  {name:'城市情绪', chip:'跟随 · 戏剧', keys:['城市','街','东京','霓虹','车','雨夜','人群']},
  {name:'奇幻想象', chip:'环绕 · 梦幻', keys:['魔法','龙','星球','宇宙','纸飞机','城堡']},
  {name:'产品展示', chip:'环绕 · 商业', keys:['产品','手机','汽车','手表','包装']}
];
const state = {mode:'text', image:null, tasks:loadTasks(), user:loadSession(), authMode:'login'};

function readJson(key, fallback){try{return JSON.parse(localStorage.getItem(key))||fallback}catch{return fallback}}
function loadTasks(){return readJson(TASKS_KEY, [])}
function loadUsers(){return readJson(USERS_KEY, {})}
function loadSession(){const email=localStorage.getItem(SESSION_KEY);return email?loadUsers()[email]||null:null}
function saveTasks(){localStorage.setItem(TASKS_KEY, JSON.stringify(state.tasks));renderTasks()}
function saveUsers(users){localStorage.setItem(USERS_KEY, JSON.stringify(users))}
function toast(message){const node=$('#toast');node.textContent=message;node.classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>node.classList.remove('show'),2400)}
function escapeHtml(text){return text.replace(/[&<>'"]/g, char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]))}

function renderAccount(){const user=state.user;$('#accountLabel').textContent=user?user.email:'登录 / 注册';$('#accountAvatar').textContent=user?user.email.slice(0,1).toUpperCase():'→';const credits=user?user.credits:100;$('#creditBalance').textContent=credits;$('#creditBar').style.width=`${credits}%`}
function openAuth(mode='login'){state.authMode=mode;$('#authModal').hidden=false;$('#authTitle').textContent=mode==='login'?'登录 MiniMax H3':'创建 MiniMax H3 账户';$('#authNote').textContent=mode==='login'?'登录后保存创作记录，并使用你的积分。':'注册即获得 100 点创作积分。';$('#authSubmit').firstChild.textContent=mode==='login'?'登录 ':'注册 ';$('#authSwitch').textContent=mode==='login'?'还没有账户？注册一个':'已有账户？返回登录';setTimeout(()=>$('#authEmail').focus(),0)}
function closeAuth(){$('#authModal').hidden=true}
function submitAuth(event){event.preventDefault();const email=$('#authEmail').value.trim().toLowerCase();const password=$('#authPassword').value;const users=loadUsers();if(state.authMode==='login'){const user=users[email];if(!user||user.password!==password){toast('邮箱或密码不正确');return}state.user=user}else{if(users[email]){toast('这个邮箱已经注册过了');return}state.user={email,password,credits:100,createdAt:Date.now()};users[email]=state.user;saveUsers(users)}localStorage.setItem(SESSION_KEY,email);closeAuth();renderAccount();toast(state.authMode==='login'?'登录成功':'注册成功，已获得 100 点积分')}
function requireCredits(){if(!state.user){openAuth();toast('请先登录后再生成视频');return false}if(state.user.credits<GENERATION_COST){toast(`积分不足，每次生成需要 ${GENERATION_COST} 点`);return false}return true}
function spendCredits(){state.user.credits-=GENERATION_COST;const users=loadUsers();users[state.user.email]=state.user;saveUsers(users);renderAccount()}

function analyzePrompt(value){return intents.find(intent=>intent.keys.some(key=>value.includes(key)))||{name:'自由创作',chip:'电影 · 缓推'}}
function updateAnalysis(){const value=$('#prompt').value.trim();$('#charCount').textContent=`${value.length} / 500`;const intent=analyzePrompt(value);$('#skillName').textContent=value?intent.name:'等待描述画面';$('#skillChip').textContent=value?intent.chip:'—';if(intent.name==='自然叙事'){$('#style').value='cinematic';$('#camera').value='aerial'}if(intent.name==='城市情绪')$('#camera').value='tracking';if(intent.name==='奇幻想象'){$('#style').value='anime';$('#camera').value='orbit'}if(intent.name==='产品展示'){$('#style').value='commercial';$('#camera').value='orbit'}}
function setMode(mode){state.mode=mode;$$('.mode-tab').forEach(tab=>{const active=tab.dataset.mode===mode;tab.classList.toggle('active',active);tab.setAttribute('aria-selected',active)});$('#imageField').hidden=mode!=='image';if(mode==='image')toast('已切换到图生视频，请上传参考画面')}
function updateFormat(){const ratio=$('#resolution').value;$('#previewFormat').textContent=`${ratio} · 1080p`;$('#previewStage').style.aspectRatio=ratio.replace(':',' / ')}
function enhance(){const value=$('#prompt').value.trim();if(!value){toast('先写下你想看到的画面');$('#prompt').focus();return}const suffix={cinematic:'电影级质感，浅景深，35mm 胶片颗粒',documentary:'纪实摄影，真实光线，手持呼吸感',anime:'细腻手绘动画，柔和色彩，流畅运动',commercial:'高端商业广告，干净布光，产品级细节'}[$('#style').value];const camera={slow_push:'镜头缓慢推进，主体始终清晰',tracking:'镜头跟随主体移动，画面稳定',orbit:'镜头环绕主体一周，展示空间层次',aerial:'航拍俯瞰，展现开阔的环境关系'}[$('#camera').value];$('#prompt').value=`${value}。${suffix}，${camera}。画面稳定，细节丰富。`.slice(0,500);updateAnalysis();toast('提示词已增强，参数也同步匹配')}

function renderTasks(){const list=$('#taskList');$('#taskCount').textContent=`${state.tasks.length} 个任务`;if(!state.tasks.length){list.innerHTML='<div class="empty-tasks"><span>○</span><div><strong>还没有生成记录</strong><p>完成一次创作后，任务会出现在这里。</p></div></div>';return}list.innerHTML=state.tasks.map(task=>`<article class="task-item"><div class="task-thumb ${task.status==='processing'?'pending':''}"></div><div class="task-copy"><strong>${escapeHtml(task.prompt)}</strong><small>${task.mode==='image'?'图生视频':'文生视频'} · ${task.duration} 秒 · ${task.resolution} · ${new Date(task.createdAt).toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'})}</small></div><div class="task-status ${task.status==='done'?'done':''}">${task.status==='processing'?'处理中 '+task.progress+'%':task.status==='done'?'已完成':'失败'} ${task.status==='failed'?`<button class="retry-button" data-retry="${task.id}">重试</button>`:''}</div></article>`).join('');$$('[data-retry]').forEach(button=>button.addEventListener('click',()=>startTask(button.dataset.retry)))}
function startTask(retryId){let task=retryId?state.tasks.find(item=>item.id===retryId):null;if(!task){const prompt=$('#prompt').value.trim();if(!prompt){toast('请先描述一个画面');$('#prompt').focus();return}if(state.mode==='image'&&!state.image){toast('图生视频需要先上传图片');return}task={id:crypto.randomUUID?crypto.randomUUID():`task-${Date.now()}`,prompt,mode:state.mode,duration:$('#duration').value,resolution:$('#resolution').value,status:'processing',progress:0,createdAt:Date.now()};state.tasks.unshift(task)}else{task.status='processing';task.progress=0}saveTasks();$('#stage-empty').hidden=true;$('#stage-result').hidden=true;$('#stage-loading').hidden=false;$('#generateButton').disabled=true;$('#generateButton span').textContent='生成中…';$('#previewShot').textContent='正在整理镜头';let tick=0;const timer=setInterval(()=>{tick+=Math.floor(Math.random()*19)+11;task.progress=Math.min(tick,100);$('#loadingText').textContent=`分析画面构成 · ${task.progress}%`;renderTasks();if(tick>=100){clearInterval(timer);const failed=Math.random()<.08;task.status=failed?'failed':'done';task.progress=100;saveTasks();$('#stage-loading').hidden=true;$('#stage-result').hidden=failed;$('#stage-empty').hidden=failed;$('#generateButton').disabled=false;$('#generateButton span').textContent='生成预览';if(!failed){$('#resultCaption').textContent=task.prompt;$('#previewShot').textContent='镜头已生成 · 可再次创作';toast('预览已生成，任务已保存到最近创作')}else toast('演示引擎暂时繁忙，可以点击任务右侧重试')}},420)}
function resetForm(){$('#prompt').value='';$('#imageUpload').value='';state.image=null;$('#imagePreview').hidden=true;setMode('text');$('#style').value='cinematic';$('#camera').value='slow_push';$('#duration').value='5';$('#resolution').value='16:9';updateAnalysis();updateFormat();$('#stage-result').hidden=true;$('#stage-loading').hidden=true;$('#stage-empty').hidden=false;$('#previewShot').textContent='等待生成';toast('已重置创作参数')}

$$('.mode-tab').forEach(tab=>tab.addEventListener('click',()=>setMode(tab.dataset.mode)));
$('#prompt').addEventListener('input',updateAnalysis);$('#enhancePrompt').addEventListener('click',enhance);$('#examplePrompt').addEventListener('click',()=>{$('#prompt').value=examples[Math.floor(Math.random()*examples.length)];updateAnalysis();toast('示例已填入')});$('#generateButton').addEventListener('click',()=>{if(!requireCredits())return;const prompt=$('#prompt').value.trim();if(!prompt||state.mode==='image'&&!state.image)return;spendCredits();startTask()});$('#resetForm').addEventListener('click',resetForm);$('#resolution').addEventListener('change',updateFormat);$('#clearHistory').addEventListener('click',()=>{state.tasks=[];saveTasks();toast('最近创作已清空')});$('#imageUpload').addEventListener('change',event=>{const file=event.target.files[0];if(!file)return;if(file.size>10*1024*1024){toast('图片不能超过 10MB');event.target.value='';return}state.image=file;const reader=new FileReader();reader.onload=event=>{$('#imagePreview img').src=event.target.result;$('#imagePreview').hidden=false};reader.readAsDataURL(file)});$('#removeImage').addEventListener('click',()=>{$('#imageUpload').value='';state.image=null;$('#imagePreview').hidden=true});
$('#accountButton').addEventListener('click',()=>state.user?toast(`${state.user.email} · 剩余 ${state.user.credits} 点积分`):openAuth());$('#authClose').addEventListener('click',closeAuth);$('#authModal').addEventListener('click',event=>{if(event.target.id==='authModal')closeAuth()});$('#authForm').addEventListener('submit',submitAuth);$('#authSwitch').addEventListener('click',()=>openAuth(state.authMode==='login'?'register':'login'));
updateAnalysis();updateFormat();renderTasks();renderAccount();

// Set localStorage.minimax-h3-api to the deployed API origin to enable the real backend.
const API_BASE = (localStorage.getItem('minimax-h3-api') || '').replace(/\/$/, '');
const API_TOKEN_KEY = 'minimax-h3-api-token';
async function apiRequest(path, options = {}) {
  const headers = {'Content-Type':'application/json', ...(options.headers || {})};
  const token = sessionStorage.getItem(API_TOKEN_KEY);
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_BASE}${path}`, {...options, headers});
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || body.message || `API ${response.status}`);
  return body;
}
async function submitRemoteAuth(event) {
  event.preventDefault();
  try {
    const email = $('#authEmail').value.trim();
    const password = $('#authPassword').value;
    const path = state.authMode === 'login' ? '/api/user/login' : '/api/user/register';
    const body = state.authMode === 'login' ? {account:email, password} : {email, password};
    const result = await apiRequest(path, {method:'POST', body:JSON.stringify(body)});
    if (result.token) sessionStorage.setItem(API_TOKEN_KEY, result.token);
    state.user = result.user || {email, credits:100};
    closeAuth(); renderAccount(); toast(state.authMode === 'login' ? '登录成功' : '注册成功');
  } catch (error) { toast(error.message); }
}
async function startRemoteTask() {
  const prompt = $('#prompt').value.trim();
  if (!prompt) { toast('请先描述一个画面'); return; }
  if (state.mode === 'image') { toast('图生视频请使用后端上传接口'); return; }
  const task = {id:`remote-${Date.now()}`, prompt, mode:state.mode, duration:$('#duration').value, resolution:$('#resolution').value, status:'processing', progress:0, createdAt:Date.now()};
  state.tasks.unshift(task); saveTasks(); $('#stage-empty').hidden=true; $('#stage-result').hidden=true; $('#stage-loading').hidden=false;
  try {
    const result = await apiRequest('/api/video/generate', {method:'POST', body:JSON.stringify({type:'text_to_video', prompt, duration:Number(task.duration), resolution:task.resolution, mode:'auto', priority:5})});
    task.id = result.task_id;
    for (let attempt=0; attempt<120; attempt += 1) {
      await new Promise(resolve=>setTimeout(resolve, 1000));
      const status = await apiRequest(`/api/video/status/${task.id}`);
      if (status.status === 'completed' || status.status === 'failed') { task.status=status.status === 'completed'?'done':'failed'; task.progress=100; task.videoUrl=status.video_url; break; }
      task.progress = Math.min(95, task.progress + 5); renderTasks();
    }
    saveTasks(); $('#stage-loading').hidden=true; $('#stage-result').hidden=task.status!=='done'; $('#stage-empty').hidden=task.status==='done'; $('#generateButton').disabled=false;
    if (task.status === 'done') { $('#resultCaption').textContent=task.prompt; $('#previewShot').textContent='H3 任务已完成'; toast('MiniMax H3 任务已完成'); } else toast('任务失败，请查看历史记录');
  } catch (error) { task.status='failed'; saveTasks(); $('#stage-loading').hidden=true; $('#stage-empty').hidden=false; $('#generateButton').disabled=false; toast(error.message); }
}
if (API_BASE) {
  $('#authForm').addEventListener('submit', submitRemoteAuth, true);
  $('#generateButton').addEventListener('click', event=>{event.stopImmediatePropagation(); if (state.user || sessionStorage.getItem(API_TOKEN_KEY)) startRemoteTask(); else openAuth();}, true);
}
