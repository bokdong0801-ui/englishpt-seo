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
})();