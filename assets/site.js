(function(){
  const modal=document.getElementById('applyModal');
  const menu=document.querySelector('[data-menu]'); const mobileNav=document.getElementById('mobileNav');
  if(menu&&mobileNav){menu.addEventListener('click',()=>{const o=menu.getAttribute('aria-expanded')==='true';menu.setAttribute('aria-expanded',String(!o));mobileNav.hidden=o;});}
  const leadClass=document.getElementById('leadClass'); const defaultClass=leadClass?.defaultValue||leadClass?.value||'잉글리시PT';
  function openForm(e){if(!modal)return;const requested=e?.currentTarget?.dataset?.course||'';if(leadClass)leadClass.value=requested||defaultClass;modal.classList.add('open');modal.setAttribute('aria-hidden','false');document.body.style.overflow='hidden';setTimeout(()=>document.getElementById('leadName')?.focus(),50);}
  function closeForm(){if(!modal)return;modal.classList.remove('open');modal.setAttribute('aria-hidden','true');document.body.style.overflow='';}
  document.querySelectorAll('[data-open-form]').forEach(x=>x.addEventListener('click',openForm));
  document.querySelectorAll('[data-close-form]').forEach(x=>x.addEventListener('click',closeForm));
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closeForm();});
  const form=document.getElementById('leadForm'); const areaInput=document.getElementById('leadArea'); const defaultArea=areaInput?.defaultValue||areaInput?.value||'';
  if(form) form.addEventListener('submit',async function(e){
    e.preventDefault(); const st=document.getElementById('leadStatus'); const btn=form.querySelector('.submit-lead');
    if(!form.reportValidity()) return;
    btn.disabled=true;btn.textContent='전송 중...';st.textContent='';
    try{
      const data=new FormData(form);
      data.set('form-name','englishpt-consultation');
      data.set('pageTitle',document.title);
      data.set('pageUrl',location.href);
      data.set('submittedAt',new Date().toISOString());
      data.set('consent','agreed');
      const res=await fetch(location.pathname,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(data).toString()});
      if(!res.ok) throw new Error('Netlify Forms submission failed: '+res.status);
      st.textContent='신청이 접수됐습니다. 남겨주신 연락처로 순차적으로 연락드리겠습니다.';
      form.reset();if(areaInput)areaInput.value=defaultArea;
    }catch(err){st.innerHTML='전송 중 문제가 발생했습니다. <a href="tel:01050068027">010-5006-8027</a> 또는 <a href="mailto:cicada3865@naver.com">cicada3865@naver.com</a>로 문의해주세요.';}
    finally{btn.disabled=false;btn.textContent='무료 PT 진단 신청 →';}
  });

  const REGION_HASH_INTENTS={
    elementary:'elem-tutor',middle:'mid-conv',high:'high-conv',
    beginner:'beginner-english-conv',adult:'adult-english-conv-academy',
    worker:'worker-english-conv-academy',university:'univ-conv',
    jobseeker:'jobseeker-conv',toeic:'toeic','toeic-speaking':'toeic-speaking',
    opic:'opic',ielts:'ielts',toefl:'toefl',duolingo:'duolingo'
  };
  document.querySelectorAll('[data-region-finder]').forEach(async finder=>{
    const sido=finder.querySelector('[data-region-sido]');
    const juris=finder.querySelector('[data-region-jurisdiction]');
    const dong=finder.querySelector('[data-region-dong]');
    const intent=finder.querySelector('[data-region-intent]');
    const go=finder.querySelector('[data-region-go]');
    const status=finder.querySelector('[data-region-status]');
    if(!sido||!juris||!dong||!intent||!go)return;
    try{
      const res=await fetch('/assets/locality-index.json',{cache:'force-cache'});
      if(!res.ok) throw new Error('region data '+res.status);
      const rows=await res.json();
      const unique=a=>[...new Set(a)].sort((x,y)=>x.localeCompare(y,'ko'));
      const option=(v,t)=>{const o=document.createElement('option');o.value=v;o.textContent=t||v;return o;};
      unique(rows.map(r=>r.sido)).forEach(v=>sido.appendChild(option(v)));
      const hash=(location.hash||'').replace('#','');
      if(REGION_HASH_INTENTS[hash]&&[...intent.options].some(o=>o.value===REGION_HASH_INTENTS[hash])) intent.value=REGION_HASH_INTENTS[hash];
      sido.addEventListener('change',()=>{
        juris.innerHTML='<option value="">시·군·구 선택</option>';
        dong.innerHTML='<option value="">읍·면·동 선택</option>'; dong.disabled=true;
        const list=unique(rows.filter(r=>r.sido===sido.value).map(r=>r.jurisdiction));
        list.forEach(v=>juris.appendChild(option(v,v.replace(sido.value+' ','')||v))); juris.disabled=!list.length;
      });
      juris.addEventListener('change',()=>{
        dong.innerHTML='<option value="">읍·면·동 선택</option>';
        const list=rows.filter(r=>r.sido===sido.value&&r.jurisdiction===juris.value).sort((a,b)=>a.dong.localeCompare(b.dong,'ko'));
        list.forEach(r=>{const o=option(r.slug,r.dong);o.dataset.slug=r.slug;dong.appendChild(o);}); dong.disabled=!list.length;
      });
      go.addEventListener('click',()=>{
        if(!dong.value||!intent.value){if(status)status.textContent='지역과 과정을 모두 선택해주세요.';return;}
        location.href='/'+dong.value+'-'+intent.value+'.html';
      });
    }catch(err){
      if(status)status.textContent='지역 목록을 불러오지 못했습니다. 역으로 찾기 또는 상담을 이용해주세요.';
    }
  });
})();