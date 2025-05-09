from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def log_captcha(request):
    """
    Log CAPTCHA information to the server terminal
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            expression = data.get('expression', 'Unknown')
            result = data.get('result', 'Unknown')
            
            # Print to terminal/console
            print(f"CAPTCHA Challenge: {expression} = {result}")
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error logging CAPTCHA: {e}")
            return JsonResponse({'status': 'error'}, status=400)
    
    return JsonResponse({'status': 'invalid method'}, status=405)

@csrf_exempt
def captcha_log(request):
    """
    Log CAPTCHA information to the server terminal
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            expression = data.get('expression', 'Unknown')
            result = data.get('result', 'Unknown')
            
            # Print to terminal in a very visible format
            print("\n" + "="*50)
            print(f"🔐 CAPTCHA CHALLENGE GENERATED")
            print(f"📝 Expression: {expression}")
            print(f"🔑 RESULT: {result}")
            print("="*50 + "\n")
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error logging CAPTCHA: {e}")
            return JsonResponse({'status': 'error'}, status=400)
    
    return JsonResponse({'status': 'invalid method'}, status=405)
