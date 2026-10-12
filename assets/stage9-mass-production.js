document.addEventListener("DOMContentLoaded",()=>{
  const form=document.querySelector("#leadForm");
  const requestType=form?.querySelector("#leadRequestType");
  const subject=form?.querySelector("#leadSubject");
  const submit=form?.querySelector('button[type="submit"]');

  const setMode=()=>{
    if(!form) return;
    if(requestType) requestType.value="체험수업 신청";
    if(subject) subject.value="ENGLISH PT 체험수업 신청";
    if(submit) submit.textContent="체험수업 신청 →";
  };
  setMode();

  document.querySelectorAll("[data-trial-cta]").forEach(a=>{
    a.addEventListener("click",()=>{
      setMode();
      setTimeout(()=>document.querySelector("#leadName")?.focus({preventScroll:true}),450);
    });
  });

  document.querySelectorAll('a[href="#consultation-preview"]').forEach(a=>{
    a.addEventListener("click",()=>setMode());
  });


  const phoneToggle=document.querySelector("[data-phone-toggle]");
  const phonePopover=document.querySelector("#header-phone-popover");
  if(phoneToggle && phonePopover){
    const closePhone=()=>{
      phonePopover.hidden=true;
      phoneToggle.setAttribute("aria-expanded","false");
    };
    phoneToggle.addEventListener("click",e=>{
      e.stopPropagation();
      const next=phonePopover.hidden;
      phonePopover.hidden=!next;
      phoneToggle.setAttribute("aria-expanded",next ? "true" : "false");
    });
    phonePopover.addEventListener("click",e=>e.stopPropagation());
    document.addEventListener("click",closePhone);
    document.addEventListener("keydown",e=>{ if(e.key==="Escape") closePhone(); });
  }

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
          btn.textContent="체험수업 신청 →";
        }
      }
    });
  });
});