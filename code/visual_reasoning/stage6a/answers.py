"""Conservative final-only scoring; unsupported answers remain unresolved."""
import ast
import math
import re
import sympy
from visual_reasoning.stage3b8.evaluation import last_boxed_expression,_strip_latex_wrappers,_replace_latex_groups


def expression(value):
    value=_replace_latex_groups(_strip_latex_wrappers(value))
    value=value.replace(r'\pi','pi').replace('π','pi').replace('²','^2').replace('³','^3')
    value=value.replace(r'\(','').replace(r'\)','').replace(r'\[','').replace(r'\]','')
    value=re.sub(r'√\s*(\d+(?:\.\d+)?)',r'sqrt(\1)',value)
    value=re.sub(r'\bsqrt(\d+(?:\.\d+)?)',r'sqrt(\1)',value)
    value=value.replace('{','(').replace('}',')').replace('^','**')
    value=re.sub(r'\s+','',value)
    value=re.sub(r'(?<=\d)(?=(?:sqrt|pi|x|\())','*',value)
    value=re.sub(r'(?<=\))(?=(?:\d|sqrt|pi|x|\())','*',value)
    if len(value)>512:raise ValueError('Expression too long')
    tree=ast.parse(value,mode='eval')
    if sum(1 for _ in ast.walk(tree))>128:raise ValueError('Expression too complex')
    def visit(node):
        if isinstance(node,ast.Constant) and type(node.value) in [int,float]:return sympy.Rational(str(node.value))
        if isinstance(node,ast.Name) and node.id in ['pi','x']:return sympy.pi if node.id=='pi' else sympy.Symbol('x',real=True)
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            result=visit(node.operand);return result if isinstance(node.op,ast.UAdd) else -result
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='sqrt' and len(node.args)==1 and not node.keywords:return sympy.sqrt(visit(node.args[0]))
        if isinstance(node,ast.BinOp):
            left,right=visit(node.left),visit(node.right)
            if isinstance(node.op,ast.Add):return left+right
            if isinstance(node.op,ast.Sub):return left-right
            if isinstance(node.op,ast.Mult):return left*right
            if isinstance(node.op,ast.Div):return left/right
            if isinstance(node.op,ast.Pow):
                if right.free_symbols or right.is_real is not True or abs(right)>8:raise ValueError('Unsupported exponent')
                return left**right
        raise ValueError('Unsupported expression node')
    result=visit(tree.body)
    if result.is_finite is False or result.is_real is False:raise ValueError('Non-finite or non-real answer')
    return result


def score_final_answer(raw,truth,complete,*,allow_arithmetic=True):
    result=dict(correctness='UNRESOLVED',predicted_answer=None,ground_truth_answer=str(truth),
        scope='Final answer only; no local visual truth or evidence-availability inference')
    if not complete or '</think>' not in raw:return {**result,'correctness':'INCOMPLETE'}
    final=raw.split('</think>',1)[1].replace('<|im_end|>','').strip()
    plain=final.replace('**','').replace('`','').strip()
    abstains=bool(re.search(r'\b(?:cannot|can\x27t|unable to)\s+(?:determine|solve|answer|read|see)|\b(?:not enough|insufficient)\s+(?:information|data)|\bno (?:image|figure|diagram) (?:is )?(?:provided|available)',plain,re.I))
    predicted=last_boxed_expression(final)
    if predicted is None:
        matches=list(re.finditer(r'(?:final\s+answer|answer)\s*(?:is|:|=)\s*([^\n]+)',plain,re.I))
        if matches:predicted=matches[-1].group(1).strip()
        elif '\n' not in plain and len(plain)<=120:predicted=plain
    if abstains and (predicted is None or re.search(r'\b(?:cannot|unable|insufficient|without|no image)\b',predicted,re.I)):
        return {**result,'correctness':'ABSTAINED','extraction_note':'Explicit inability/insufficient-image statement'}
    if predicted is None:return {**result,'extraction_note':'No supported final answer form'}
    predicted=predicted.strip().strip('$').strip(' .');result['predicted_answer']=predicted
    if re.search(r'\b(?:maybe|might|perhaps|could|or)\b',predicted,re.I):return {**result,'extraction_note':'Ambiguous final expression'}
    expected=str(truth).strip()
    if not allow_arithmetic and ' '.join(predicted.casefold().split())==' '.join(expected.casefold().split()):
        return {**result,'correctness':'CORRECT','comparison':'Literal document field; case and whitespace normalization only'}
    if re.fullmatch(r'[A-Za-z][A-Za-z -]{0,63}',expected) and re.fullmatch(r'[A-Za-z][A-Za-z -]{0,63}',predicted):
        if len(predicted.split())>len(expected.split())+1:return {**result,'extraction_note':'Prose answer requires review'}
        return {**result,'correctness':'CORRECT' if predicted.casefold()==expected.casefold() else 'INCORRECT','comparison':'Exact categorical value'}
    plain_number=r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)'
    if not allow_arithmetic and not all(re.fullmatch(plain_number,v) for v in [predicted,expected]):
        return {**result,'extraction_note':'Nonidentical document field requires review; phone/date/range punctuation is not arithmetic'}
    try:
        pred_expr=expression(predicted);truth_expr=expression(expected);difference=sympy.simplify(pred_expr-truth_expr)
        correct=difference==0
        if not correct and not difference.free_symbols:
            error=float(abs(sympy.N(difference)));scale=max(1.0,abs(float(sympy.N(truth_expr))))
            correct=math.isfinite(error) and error<=1e-8*scale
        return {**result,'correctness':'CORRECT' if correct else 'INCORRECT',
            'comparison':'Bounded explicit arithmetic/sqrt/pi/x expression; exact symbolic or1e-8relative numeric agreement',
            'normalized_prediction':str(pred_expr),'normalized_truth':str(truth_expr)}
    except (ValueError,TypeError,SyntaxError,ZeroDivisionError,OverflowError) as error:
        return {**result,'extraction_note':str(error)}


def score_condition_answer(row):
    """Separate answer agreement from truth/visibility in the presented condition.

    The caller joins original C1 source answers from the intact manifest. A
    counterfactual must never silently inherit its changed answer as source truth.
    """
    if row['cohort']=='C1' and row['condition']=='counterfactual':
        assert 'source_answer' in row, 'Join the intact source answer before scoring'
    source_truth=row.get('source_answer',row['answer'])
    source=score_final_answer(row['raw_decoded_response'],source_truth,row['complete'],allow_arithmetic=row['cohort']!='C2')
    condition=score_final_answer(row['raw_decoded_response'],row['answer'],row['complete'],allow_arithmetic=row['cohort']!='C2')
    availability='source-derived task truth; visibility/causal use not established by answer matching'
    applies=True
    if row['condition']=='no_image' or (row['cohort']=='C1' and row['condition']=='unrelated'):
        applies=False;availability='No task source image; source-answer consistency only'
    elif row['condition']=='mask':
        applies=False;availability='Target pixels masked; remaining context/hidden-object interpretation cannot establish presented-image truth'
    elif row['cohort']=='C3' and row['condition']=='unrelated':
        availability='Independently reviewed queried-category absence in actual donor image; original source answer separate'
    label=condition['correctness']
    if not applies and label in ['CORRECT','INCORRECT']:label='UNRESOLVED'
    object_label='NOT_ASSIGNED_BY_FINAL_ANSWER_SCORER'
    if row['cohort']=='C3':
        object_label='UNRESOLVED_VISIBILITY_AND_ASSERTION' if not applies else 'REQUIRES_ASSERTION_REVIEW'
    return dict(final_answer_correctness=label,final_readout=condition['predicted_answer'],
        source_answer=str(source_truth),condition_answer=str(row['answer']),
        source_answer_consistency={'CORRECT':'CONSISTENT','INCORRECT':'INCONSISTENT'}.get(source['correctness'],source['correctness']),
        condition_answer_applicability=availability,condition_truth_applicable=applies,
        local_visual_correctness='UNRESOLVED',object_hallucination_presence=object_label,
        source_answer_score=source,condition_reference_score=condition,
        review_note='Conservative deterministic final-only parser. Source agreement does not establish local visual truth, causal use or mirage.',
        annotation_method='automatic_final_only',attention_or_causal_data_used=False)
