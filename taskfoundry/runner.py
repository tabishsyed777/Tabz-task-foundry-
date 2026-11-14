"""Candidate-only execution entrypoint: receives inputs, never expected answers."""
import json
import runpy
import os
import resource
import sys


def main():
    resource.setrlimit(resource.RLIMIT_CPU,(3,3))
    resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
    resource.setrlimit(resource.RLIMIT_FSIZE,(1024*1024,1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
    args=sys.argv[1:]
    if args[0]=='--drop-uid':
        os.setgroups([]);os.setgid(65534);os.setuid(65534);args=args[1:]
    inputs=json.load(sys.stdin)
    transform=runpy.run_path(args[0])['transform']
    outputs=[transform(item) for item in inputs]
    print(json.dumps(outputs,allow_nan=False,separators=(',',':')))

if __name__=='__main__':main()
