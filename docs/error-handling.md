---
title: Error Handling
---

# Error Handling

mdxlate is designed to be resilient and continue processing even when individual translations fail. It includes comprehensive error handling, failure reporting, and recovery mechanisms.

## How Error Handling Works

### Graceful Failure

When a translation fails, mdxlate:

1. **Logs the error** with details
2. **Continues processing** other files
3. **Saves successful translations** to cache
4. **Generates a failure report** for retry

This ensures that temporary API issues or rate limits don't stop your entire translation workflow.

### Failure Report

Failed translations are tracked in:
```
<source_dir>/.mdxlate.failures.json
```

**Example report:**
```json
{
  "failures": [
    {
      "file": "docs/advanced.md",
      "error": "Rate limit exceeded",
      "error_type": "RateLimitError"
    },
    {
      "file": "docs/api/reference.md", 
      "error": "Connection timeout",
      "error_type": "APIConnectionError"
    }
  ]
}
```

## Common Error Types

### API Errors

#### Rate Limit Errors

**Symptom:**
```
RateLimitError: Rate limit exceeded
```

**Cause:** Too many requests to the API in a short time.

**Solution:**

1. **Wait and retry:**
   ```bash
   # Wait a few minutes, then re-run
   mdx run docs output --languages de fr
   # Only failed files will be retried (cache helps!)
   ```

2. **Reduce concurrency** (programmatic only):
   ```python
   from mdxlate.translator import Translator
   from mdxlate.client import make_client
   
   translator = Translator(
       client=make_client(provider="openai", api_key="sk-..."),
       base_language="en",
       languages=["de"],
       model="gpt-4o-mini",
       max_concurrency=4,  # Reduce from default 8
   )
   ```

3. **Use different provider:**
   ```bash
   mdx run docs output --languages de --provider openrouter
   ```

#### Authentication Errors

**Symptom:**
```
AuthenticationError: Invalid API key
```

**Cause:** Missing, expired, or incorrect API key.

**Solution:**

1. **Check environment variable:**
   ```bash
   echo $OPENAI_API_KEY
   # Should output: sk-...
   ```

2. **Set correct API key:**
   ```bash
   export OPENAI_API_KEY=sk-your-actual-key
   mdx run docs output --languages de
   ```

3. **Pass key explicitly:**
   ```bash
   mdx run docs output --languages de --api-key sk-your-key
   ```

#### Connection Errors

**Symptom:**
```
APIConnectionError: Connection timeout
```

**Cause:** Network issues or API endpoint unreachable.

**Solution:**

1. **Check internet connection:**
   ```bash
   ping api.openai.com
   ```

2. **Retry the operation:**
   ```bash
   mdx run docs output --languages de
   # Failed files will be retried
   ```

3. **Use custom base URL:**
   ```bash
   mdx run docs output --languages de --base-url https://api.openai.com/v1
   ```

### File System Errors

#### Permission Errors

**Symptom:**
```
PermissionError: Cannot write to directory
```

**Cause:** No write permission for output directory.

**Solution:**

1. **Check permissions:**
   ```bash
   ls -ld output/
   ```

2. **Fix permissions:**
   ```bash
   chmod 755 output/
   mdx run docs output --languages de
   ```

3. **Use different output directory:**
   ```bash
   mdx run docs ~/translations --languages de
   ```

#### Disk Space Errors

**Symptom:**
```
OSError: No space left on device
```

**Cause:** Insufficient disk space.

**Solution:**

1. **Check disk space:**
   ```bash
   df -h
   ```

2. **Free up space or use different location:**
   ```bash
   mdx run docs /mnt/storage/output --languages de
   ```

### Source/Output Conflicts

#### Source Inside Output Error

**Symptom:**
```
ValueError: Source directory cannot be inside output directory
```

**Cause:** Source directory is a subdirectory of output directory.

**Solution:**

```bash
# Wrong
mdx run output/docs output --languages de

# Correct
mdx run docs output --languages de
```

## Retry Mechanism

### Automatic Retries

mdxlate uses exponential backoff for transient errors:

```python
# Built-in retry logic (from code)
@tenacity.retry(
    wait=wait_exponential(multiplier=2, min=2, max=60),
    stop=stop_after_attempt(6)
)
async def translate_text(self, content: str, target_language: str) -> str:
    # Translation logic with automatic retry
```

**Retry strategy:**
- Attempt 1: Immediate
- Attempt 2: Wait 2 seconds
- Attempt 3: Wait 4 seconds  
- Attempt 4: Wait 8 seconds
- Attempt 5: Wait 16 seconds
- Attempt 6: Wait 32 seconds
- After 6 attempts: Report failure

### Manual Retry

Simply re-run the command:

```bash
# First run (some failures)
mdx run docs output --languages de fr

# Check failures
cat docs/.mdxlate.failures.json

# Retry (only failed files processed)
mdx run docs output --languages de fr
```

The cache ensures only failed files are retried!

## Checking for Failures

### CLI Check

```bash
# Run translation
mdx run docs output --languages de fr

# Check for failures
if [ -f "docs/.mdxlate.failures.json" ]; then
  echo "Some translations failed!"
  cat docs/.mdxlate.failures.json
  exit 1
fi
```

### Programmatic Check

```python
import json
from pathlib import Path
from mdxlate.start_translation import start_translation

docs_src = Path("docs")
out_dir = Path("output")

# Run translation
start_translation(
    docs_src=docs_src,
    out_dir=out_dir,
    base_language="en",
    languages=["de", "fr"],
)

# Check for failures
failure_report = docs_src / ".mdxlate.failures.json"
if failure_report.exists():
    failures = json.loads(failure_report.read_text())
    print(f"⚠️  {len(failures['failures'])} files failed to translate:")
    
    for failure in failures['failures']:
        print(f"  - {failure['file']}: {failure['error']}")
    
    # Handle failures (e.g., send alert, retry, etc.)
    raise RuntimeError("Translation incomplete")
else:
    print("✓ All translations successful!")
```

## Error Recovery Strategies

### Strategy 1: Automatic Retry Loop

```bash
#!/bin/bash

MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  mdx run docs output --languages de fr
  
  if [ ! -f "docs/.mdxlate.failures.json" ]; then
    echo "✓ Translation successful!"
    exit 0
  fi
  
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "Attempt $RETRY_COUNT failed, retrying in 30s..."
  sleep 30
done

echo "✗ Translation failed after $MAX_RETRIES attempts"
exit 1
```

### Strategy 2: Progressive Translation

```bash
# Translate one language at a time
for lang in de fr es; do
  echo "Translating to $lang..."
  mdx run docs output --languages $lang
  
  if [ -f "docs/.mdxlate.failures.json" ]; then
    echo "Failures in $lang, retrying..."
    mdx run docs output --languages $lang
  fi
done
```

### Strategy 3: Failure Notification

```python
import json
import smtplib
from pathlib import Path
from email.message import EmailMessage
from mdxlate.start_translation import start_translation

def send_failure_alert(failures):
    msg = EmailMessage()
    msg['Subject'] = 'Translation Failures Detected'
    msg['From'] = 'alerts@example.com'
    msg['To'] = 'admin@example.com'
    msg.set_content(f"Failed translations:\n\n{json.dumps(failures, indent=2)}")
    
    with smtplib.SMTP('localhost') as s:
        s.send_message(msg)

# Run translation
docs_src = Path("docs")
start_translation(
    docs_src=docs_src,
    out_dir=Path("output"),
    base_language="en",
    languages=["de", "fr"],
)

# Check and alert
failure_report = docs_src / ".mdxlate.failures.json"
if failure_report.exists():
    failures = json.loads(failure_report.read_text())
    send_failure_alert(failures)
```

## CI/CD Error Handling

### GitHub Actions

```yaml
name: Translate Docs

on:
  push:
    branches: [main]

jobs:
  translate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install uv
        uses: astral-sh/setup-uv@v6
      
      - name: Install mdxlate
        run: uv pip install mdxlate
      
      - name: Initialize prompt
        run: mdx init
      
      - name: Translate documentation
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          mdx run docs output --languages de fr --cache-dir /tmp
      
      - name: Check for failures
        run: |
          if [ -f "docs/.mdxlate.failures.json" ]; then
            echo "::error::Translation failures detected"
            cat docs/.mdxlate.failures.json
            exit 1
          fi
      
      - name: Upload translations
        uses: actions/upload-artifact@v3
        with:
          name: translations
          path: output/
      
      - name: Upload failures (if any)
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: translation-failures
          path: docs/.mdxlate.failures.json
```

### GitLab CI

```yaml
translate:
  image: python:3.10
  
  script:
    - pip install mdxlate
    - mdx init
    - mdx run docs output --languages de fr --cache-dir /tmp
    
    # Check for failures
    - |
      if [ -f "docs/.mdxlate.failures.json" ]; then
        echo "Translation failures detected:"
        cat docs/.mdxlate.failures.json
        exit 1
      fi
  
  artifacts:
    paths:
      - output/
    when: on_success
    
  artifacts:
    paths:
      - docs/.mdxlate.failures.json
    when: on_failure
    expire_in: 1 week
  
  retry:
    max: 2
    when:
      - api_failure
      - runner_system_failure
```

### Jenkins

```groovy
pipeline {
    agent any
    
    environment {
        OPENAI_API_KEY = credentials('openai-api-key')
    }
    
    stages {
        stage('Translate') {
            steps {
                sh 'pip install mdxlate'
                sh 'mdx init'
                sh 'mdx run docs output --languages de fr'
            }
        }
        
        stage('Check Failures') {
            steps {
                script {
                    if (fileExists('docs/.mdxlate.failures.json')) {
                        def failures = readFile('docs/.mdxlate.failures.json')
                        error("Translation failures:\n${failures}")
                    }
                }
            }
        }
    }
    
    post {
        success {
            archiveArtifacts artifacts: 'output/**', fingerprint: true
        }
        failure {
            archiveArtifacts artifacts: 'docs/.mdxlate.failures.json', fingerprint: true
            emailext(
                subject: "Translation Failed: ${env.JOB_NAME}",
                body: "Check console output and failure report",
                to: 'team@example.com'
            )
        }
    }
}
```

## Debugging Translation Errors

### Enable Detailed Logging

```python
import logging
from pathlib import Path
from mdxlate.start_translation import start_translation

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation.log'),
        logging.StreamHandler()
    ]
)

start_translation(
    docs_src=Path("docs"),
    out_dir=Path("output"),
    base_language="en",
    languages=["de", "fr"],
)

# Check log file for detailed error information
print("Check translation.log for details")
```

### Isolate Problematic Files

```bash
# Test single file
mdx run problem-file/ output --languages de --force

# If successful, issue is with concurrent processing
# If fails, issue is with the file or prompt
```

### Validate API Connection

```python
from mdxlate.client import make_client
import asyncio

async def test_api():
    client = make_client(provider="openai", api_key="sk-...")
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}]
    )
    
    print("API connection successful!")
    print(f"Response: {response.choices[0].message.content}")

asyncio.run(test_api())
```

## Best Practices

1. **Always check failure reports** after translation runs
2. **Use cache** to avoid re-translating successful files on retry
3. **Implement retry logic** for production environments
4. **Monitor API quotas** to avoid rate limits
5. **Log errors** for debugging and monitoring
6. **Set up alerts** for critical failures in CI/CD
7. **Test with small batches** before large-scale translation
8. **Keep backups** of original files

## Troubleshooting Guide

| Issue | Cause | Solution |
|-------|-------|----------|
| All files failing | API key issue | Verify `OPENAI_API_KEY` is set correctly |
| Intermittent failures | Rate limiting | Reduce concurrency or wait between runs |
| Specific files failing | File content issue | Check file for unusual formatting |
| No error message | Silent failure | Enable debug logging |
| Cache not working | Cache file deleted | Check `.mdxlate.hashes.json` exists |
| Slow translation | High concurrency | Network or API limits, reduce concurrency |

## See Also

- [CLI Reference](cli.md) - Command-line error handling
- [Programmatic Usage](programmatic.md) - Error handling in Python
- [Caching System](caching.md) - How cache helps with retries
- [FAQ](faq.md) - Common issues and solutions
