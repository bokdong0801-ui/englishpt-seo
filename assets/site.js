
(function(){
  const modal=document.getElementById('applyModal');
  const menu=document.querySelector('[data-menu]'); const mobileNav=document.getElementById('mobileNav');
  if(menu&&mobileNav){menu.addEventListener('click',()=>{const o=menu.getAttribute('aria-expanded')==='true';menu.setAttribute('aria-expanded',String(!o));mobileNav.hidden=o;});}
  function openForm(){if(!modal)return;modal.classList.add('open');modal.setAttribute('aria-hidden','false');document.body.style.overflow='hidden';setTimeout(()=>document.getElementById('leadName')?.focus(),50);}
  function closeForm(){if(!modal)return;modal.classList.remove('open');modal.setAttribute('aria-hidden','true');document.body.style.overflow='';}
  document.querySelectorAll('[data-open-form]').forEach(x=>x.addEventListener('click',openForm));
  document.querySelectorAll('[data-close-form]').forEach(x=>x.addEventListener('click',closeForm));
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closeForm();});
  const form=document.getElementById('leadForm'); const areaInput=document.getElementById('leadArea'); const defaultArea=areaInput?.defaultValue||areaInput?.value||'';
  if(window.emailjs){try{emailjs.init({publicKey:'eJdMKTqwA8M35JTQJsGTd'})}catch(e){}}
  if(form) form.addEventListener('submit',async function(e){
    e.preventDefault(); const st=document.getElementById('leadStatus'); const btn=form.querySelector('.submit-lead');
    if(!form.reportValidity()) return;
    const diff=form.querySelector('input[name="difficulty"]:checked')?.value||'';
    const raw=document.getElementById('leadMessage').value.trim();
    const msg='[목적] '+document.getElementById('leadPurpose').value+'\n[현재 어려움] '+diff+'\n[추가 문의] '+(raw||'(없음)');
    btn.disabled=true;btn.textContent='전송 중...';st.textContent='';
    try{
      if(!window.emailjs) throw new Error('EmailJS unavailable');
      await emailjs.send('service_r1950hf','template_mqovosk',{name:document.getElementById('leadName').value.trim(),phone:document.getElementById('leadPhone').value.trim(),area:document.getElementById('leadArea').value.trim(),wantedClass:document.getElementById('leadClass').value,message:msg,pageTitle:document.title,pageUrl:location.href});
      st.textContent='신청이 접수됐습니다. 남겨주신 연락처로 순차적으로 연락드리겠습니다.';form.reset();if(areaInput)areaInput.value=defaultArea;
    }catch(err){st.innerHTML='전송 중 문제가 발생했습니다. <a href="tel:01050068027">010-5006-8027</a>로 문의해주세요.';}
    finally{btn.disabled=false;btn.textContent='무료 PT 진단 신청 →';}
  });
})();
