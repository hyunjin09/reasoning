"""Conservative local answer extraction; unresolved is distinct from wrong."""
import ast
import math
import operator
import re


def extract_final(text, *, normal_eos=True):
    # Native Thinking traces must expose their final-answer boundary.
    if '</think>' not in text:
        return None
    final=text.rsplit('</think>',1)[1].replace('<|im_end|>','').strip()
    starts=list(re.finditer(r'\\(?:boxed|fbox)\s*\{',final))
    if starts:
        start=starts[-1].end();depth=1
        for i in range(start,len(final)):
            if final[i]=='{':depth+=1
            elif final[i]=='}':depth-=1
            if depth==0:return final[start:i].strip()
        return None
    match=re.search(r'(?:final answer|answer)\s*[:=]\s*([^\n]+)\s*$',final,re.I)
    if match:return match.group(1).strip().strip('$')
    if normal_eos and re.fullmatch(r'\(?[A-E]\)?\.?',final):return final.strip('().')
    return None


def normalized(text):
    text=str(text).strip().strip('$').strip().rstrip('.')
    for pattern in [r'\\left',r'\\right',r'\\,',r'\\!',r'\\;',r'\\quad']:
        text=re.sub(pattern,'',text)
    text=re.sub(r'\\(?:mathrm|text)\{([^{}]*)\}',r'\1',text)
    return re.sub(r'\s+','',text).lower()


def safe_number(text):
    text=normalized(text)
    if not text or len(text)>512:return None
    for _ in range(12):
        changed=re.sub(r'\\(?:dfrac|tfrac|frac)\{([^{}]*)\}\{([^{}]*)\}',r'((\1)/(\2))',text)
        changed=re.sub(r'\\sqrt\{([^{}]*)\}',r'sqrt(\1)',changed)
        if changed==text:break
        text=changed
    text=text.replace(r'\pi','pi').replace('π','pi').replace(r'\times','*').replace(r'\cdot','*').replace('^','**').replace('−','-')
    text=text.replace('{','(').replace('}',')')
    text=re.sub(r'(\d|\))(pi|sqrt\()',r'\1*\2',text)
    if text.endswith('%'):text='('+text[:-1]+')/100'
    ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}
    def visit(node):
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):return float(node.value)
        if isinstance(node,ast.Name) and node.id=='pi':return math.pi
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            return visit(node.operand)*(1 if isinstance(node.op,ast.UAdd) else -1)
        if isinstance(node,ast.BinOp):
            a,b=visit(node.left),visit(node.right)
            if type(node.op) in ops:return ops[type(node.op)](a,b)
            if isinstance(node.op,ast.Pow) and abs(b)<=16 and abs(a)<=1e12:return a**b
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='sqrt' and len(node.args)==1 and not node.keywords:
            return math.sqrt(visit(node.args[0]))
        raise ValueError('Unsupported arithmetic')
    try:
        tree=ast.parse(text,mode='eval')
        if sum(1 for _ in ast.walk(tree))>80:return None
        value=visit(tree.body)
        return float(value) if isinstance(value,(int,float)) and math.isfinite(value) and abs(value)<1e100 else None
    except (ValueError,SyntaxError,TypeError,OverflowError,ZeroDivisionError,RecursionError):return None


def equivalent(a,b):
    if normalized(a)==normalized(b):return True
    left,right=safe_number(a),safe_number(b)
    if left is None or right is None:return None
    # Benchmark-authored MATH-V evaluation/utils.py uses two-decimal equality.
    return round(left,2)==round(right,2)


def score_answer(text,row,*,normal_eos=True):
    answer=extract_final(text,normal_eos=normal_eos)
    result=dict(extracted=answer,correct=None,status='unresolved',method='final-section balanced box / bounded arithmetic / official two-decimal equality')
    if answer is None:return result
    options=row['options'];gt=row['answer']
    if options:
        letter=answer.strip().strip('().').upper()
        if len(letter)==1 and 'A'<=letter<chr(65+len(options)):
            result.update(correct=letter==gt,status='scored',option=letter);return result
        matches=[i for i,o in enumerate(options) if equivalent(answer,o) is True]
        if len(matches)==1:
            result.update(correct=chr(65+matches[0])==gt,status='scored',option=chr(65+matches[0]));return result
        # A numeric answer unequal to every numeric option is an identifiable mismatch.
        if safe_number(answer) is not None and all(safe_number(o) is not None for o in options) and not matches:
            result.update(correct=False,status='scored');return result
    else:
        result['correct']=equivalent(answer,gt)
        if result['correct'] is not None:result['status']='scored'
    return result
