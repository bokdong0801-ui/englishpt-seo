#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GET-only Netlify credit/billing status diagnostic. No account/site mutations."""
import json, os, urllib.request, urllib.error, sys, datetime
from pathlib import Path
ROOT='https://api.netlify.com/api/v1'
OUT=Path('netlify-credit-diagnostic')
OUT.mkdir(exist_ok=True)
SITE='98d96cc5-f0b7-4d3d-8072-6476d93e55a3'

def fetch(path,token):
    req=urllib.request.Request(ROOT+path,headers={'Authorization':'Bearer '+token,'Accept':'application/json','User-Agent':'englishpt-credit-readonly-20261017'},method='GET')
    with urllib.request.urlopen(req,timeout=35) as response:
        return json.load(response)
def safe_num(x):
    return x if isinstance(x,(int,float)) and not isinstance(x,bool) else None
def summarize_credit(x):
    if not isinstance(x,dict):return None
    whitelist=('included','used','remaining','available','limit','total','granted','operational','balance','plan','monthly','consumed','exceeded','overages','amount','unit')
    output={}
    for k in whitelist:
        v=x.get(k)
        if isinstance(v,(int,float,bool)) or isinstance(v,str) and k=='unit':
            output[k]=v
    return output
def main():
    result={'status':'HOLD_PENDING_DIAGNOSTIC','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'site_id':SITE,'production_deployed':False,'credit_purchased':False,'plan_changed':False,'netlify_post_requests':0,
      'error':None}
    try:
        token=os.environ['NETLIFY_AUTH_TOKEN']
        site=fetch('/sites/'+SITE,token)
        assert site.get('id')==SITE, 'Unexpected site identity'
        account=fetch('/accounts/'+site['account_id'],token)
        caps=account.get('capabilities') or {}
        # Allowlist only. No personal billing details, tokens, payment methods, invoices or emails.
        record={
          'team_slug':account.get('slug'),
          'account_id':site['account_id'],
          'plan':account.get('type_name') or account.get('type'),
          'billing_period':account.get('billing_period'),
          'in_operational_mode':account.get('in_operational_mode'),
          'usages_exceeded':account.get('usages_exceeded'),
          'configurable_limits_exceeded':account.get('configurable_limits_exceeded'),
          'sites_with_usage_exceeded_count':len(account.get('sites_with_usage_exceeded') or []),
          'plan_credits':safe_num(account.get('plan_credits')),
          'credit_capabilities':summarize_credit(caps.get('credits')),
          'credit_related_capability_keys':sorted(k for k in caps if 'credit' in k.lower() or 'usage' in k.lower()),
          'account_credit_related_field_keys':sorted(k for k in account if any(term in k.lower() for term in ('credit','usage','operational','billing_period','subscription','trial','payment_required','overdue'))),
          'block_builds_when_usage_exceeded':caps.get('block_builds_when_usage_exceeded'),
          'accumulate_overages':caps.get('accumulate_overages'),
          'site_state':site.get('state'),
          'site_disabled':site.get('disabled'),
          'prevent_non_git_prod_deploys':site.get('prevent_non_git_prod_deploys'),
          'published_deploy_id':(site.get('published_deploy') or {}).get('id')
        }
        # Examine only most recent deploy statuses, no artifacts / secrets / build logs.
        history=fetch('/sites/'+SITE+'/deploys?per_page=12',token)
        record['last_deploys']=[{
           'id':d.get('id'),'state':d.get('state'),'context':d.get('context'),
           'created_at':d.get('created_at'),'published_at':d.get('published_at'),
           'locked':d.get('locked'),'error_excerpt':(d.get('error_message') or '')[:140]
        } for d in history[:12]]
        grant=record['credit_capabilities'] or {}
        # Distinguish situations without claiming flag false itself uniquely implies a cause.
        included=grant.get('included')
        used=grant.get('used')
        left=grant.get('remaining')
        if left is None and included is not None and used is not None:left=included-used
        record['computed_remaining_from_api_if_available']=left
        blocked=(record['in_operational_mode'] is False)
        limits=bool(record['usages_exceeded'] or record['configurable_limits_exceeded'])
        if blocked and left is not None and left>0 and not limits:
            record['diagnosis']='POSSIBLE_ACCOUNT_STATE_CREDIT_FLAG_INCONSISTENCY'
        elif blocked and (left is not None and left<=0 or limits):
            record['diagnosis']='CREDIT_EXHAUSTION_OR_USAGE_RESTRICTION_POSSIBLE'
        elif blocked:
            record['diagnosis']='BLOCKED_BUT_CREDIT_BALANCE_NOT_CONFIRMED'
        else:
            record['diagnosis']='NO_CURRENT_OPERATING_MODE_FALSE_FLAG'
        result.update({'status':'PASS_READONLY_DIAGNOSTIC_PRODUCTION_STILL_HOLD' if blocked else 'PASS_READONLY_DIAGNOSTIC_NO_FLAG_BLOCK',
                        'account_status':record})
    except Exception as e:
        result['status']='HOLD_DIAGNOSTIC_FAILED'
        result['error']=type(e).__name__+': '+str(e)[:160]
    finally:
        (OUT/'NETLIFY_CREDIT_ACCOUNT_DIAGNOSTIC.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        print('NETLIFY_ACCOUNT_CREDIT_DIAGNOSTIC',json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result['status'].startswith('PASS_') else 1
if __name__=='__main__':sys.exit(main())
