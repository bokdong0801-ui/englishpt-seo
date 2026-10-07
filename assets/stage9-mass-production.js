document.addEventListener("DOMContentLoaded",()=>{
  const forms=document.querySelectorAll("#pilotForm,#leadForm");
  if(window.emailjs){try{emailjs.init({publicKey:"eJdMKTqwA8M35JTQJsGTd",blockHeadless:true,limitRate:{id:"englishpt-lead",throttle:10000}});}catch(e){}}
  forms.forEach(form=>{
    form.addEventListener("submit",async e=>{
      e.preventDefault();
      if(!form.reportValidity()) return;
      const status=form.querySelector(".pilot-status,.lead-status");
      const btn=form.querySelector('button[type="submit"]');
      const name=form.querySelector('[name="name"]')?.value.trim()||"";
      const phone=form.querySelector('[name="phone"]')?.value.trim()||"";
      const area=form.querySelector('[name="area"]')?.value.trim()||"";
      const extra=form.querySelector('[name="message"]')?.value.trim()||"";
      const wantedClass=form.querySelector('[name="wantedClass"]')?.value.trim()||document.querySelector("h1")?.textContent.trim()||document.title;
      const message="[문의내용] "+(extra||"(미입력)");
      if(btn){btn.disabled=true;btn.textContent="전송 중...";}
      if(status) status.textContent="";
      try{
        if(!window.emailjs) throw new Error("EmailJS unavailable");
        await emailjs.send("service_r1950hf","template_mqovosk",{
          name,phone,area,wantedClass,message,pageTitle:document.title,pageUrl:location.href,consent:"agreed",submittedAt:new Date().toISOString(),to_email:"cicada3865@naver.com",reply_to:"cicada3865@naver.com"
        });
        if(status) status.textContent="신청이 접수됐습니다. 남겨주신 연락처로 순차적으로 연락드리겠습니다.";
        form.reset();
      }catch(err){
        if(status) status.innerHTML='전송 중 문제가 발생했습니다. <a href="tel:+821050068027">010-5006-8027</a> 또는 <a href="mailto:cicada3865@naver.com">cicada3865@naver.com</a>로 문의해주세요.';
      }finally{
        if(btn){btn.disabled=false;btn.textContent="무료 PT 진단 신청 →";}
      }
    });
  });
});