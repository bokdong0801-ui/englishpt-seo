document.addEventListener("DOMContentLoaded",()=>{
  const form=document.querySelector("#leadForm");
  const requestType=form?.querySelector("#leadRequestType");
  const subject=form?.querySelector("#leadSubject");
  const submit=form?.querySelector('button[type="submit"]');

  const setMode=(mode)=>{
    if(!form) return;
    const trial=mode==="trial";
    if(requestType) requestType.value=trial ? "체험수업 신청" : "무료 PT 진단";
    if(subject) subject.value=trial ? "ENGLISH PT 체험수업 신청" : "ENGLISH PT 새 상담 신청";
    if(submit) submit.textContent=trial ? "체험수업 신청 →" : "무료 PT 진단 신청 →";
  };

  document.querySelectorAll("[data-trial-cta]").forEach(a=>{
    a.addEventListener("click",()=>{
      setMode("trial");
      setTimeout(()=>document.querySelector("#leadName")?.focus({preventScroll:true}),450);
    });
  });

  document.querySelectorAll('a[href="#consultation-preview"]:not([data-trial-cta])').forEach(a=>{
    a.addEventListener("click",()=>setMode("diagnosis"));
  });

  const forms=document.querySelectorAll("#pilotForm,#leadForm");
  forms.forEach(form=>{
    form.addEventListener("submit",async e=>{
      e.preventDefault();
      if(!form.reportValidity()) return;
      const status=form.querySelector(".pilot-status,.lead-status");
      const btn=form.querySelector('button[type="submit"]');
      if(btn){btn.disabled=true;btn.textContent="전송 중...";}
      if(status) status.textContent="";
      try{
        const data=new FormData(form);
        data.set("form-name","englishpt-consultation");
        data.set("pageTitle",document.title);
        data.set("pageUrl",location.href);
        data.set("submittedAt",new Date().toISOString());
        data.set("consent","agreed");
        const res=await fetch(location.pathname,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams(data).toString()});
        if(!res.ok) throw new Error("Netlify Forms submission failed: "+res.status);
        if(status) status.textContent="신청이 접수됐습니다. 남겨주신 연락처로 순차적으로 연락드리겠습니다.";
        form.reset();
      }catch(err){
        if(status) status.innerHTML='전송 중 문제가 발생했습니다. <a href="tel:+821050068027">010-5006-8027</a> 또는 <a href="mailto:cicada3865@naver.com">cicada3865@naver.com</a>로 문의해주세요.';
      }finally{
        if(btn){
          btn.disabled=false;
          const trial=form.querySelector("#leadRequestType")?.value==="체험수업 신청";
          btn.textContent=trial ? "체험수업 신청 →" : "무료 PT 진단 신청 →";
        }
      }
    });
  });
});