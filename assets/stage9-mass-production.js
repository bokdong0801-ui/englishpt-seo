document.addEventListener("DOMContentLoaded",()=>{
  const forms=document.querySelectorAll("#pilotForm");
  if(window.emailjs){
    try{emailjs.init({publicKey:"eJdMKTqwA8M35JTQJsGTd"});}catch(e){}
  }
  forms.forEach(form=>{
    form.addEventListener("submit",async e=>{
      e.preventDefault();
      const status=form.querySelector(".pilot-status");
      const btn=form.querySelector('button[type="submit"]');
      if(!form.reportValidity()) return;
      const name=form.querySelector('[name="name"]')?.value.trim()||"";
      const phone=form.querySelector('[name="phone"]')?.value.trim()||"";
      const deadline=form.querySelector('[name="deadline"]')?.value.trim()||"";
      const difficulty=form.querySelector('[name="difficulty"]')?.value.trim()||"";
      const h1=document.querySelector("h1")?.textContent.trim()||document.title;
      const area=(h1.split(/\s+/)[0]||"").trim();
      const message="[가까운 일정] "+(deadline||"(미입력)")+"\n[가장 막히는 장면] "+(difficulty||"(미입력)");
      if(btn){btn.disabled=true;btn.textContent="전송 중...";}
      if(status) status.textContent="";
      try{
        if(!window.emailjs) throw new Error("EmailJS unavailable");
        await emailjs.send("service_r1950hf","template_mqovosk",{
          name,phone,area,
          wantedClass:h1,
          message,
          pageTitle:document.title,
          pageUrl:location.href
        });
        if(status) status.textContent="신청이 접수됐습니다. 남겨주신 연락처로 순차적으로 연락드리겠습니다.";
        form.reset();
      }catch(err){
        if(status) status.innerHTML='전송 중 문제가 발생했습니다. <a href="tel:+821050068027">010-5006-8027</a>로 문의해주세요.';
      }finally{
        if(btn){btn.disabled=false;btn.textContent="무료 PT 진단 신청 →";}
      }
    });
  });
});