import init_script

from pywikibot.pagegenerators import GeneratorFactory


gen = GeneratorFactory()
gen.handle_args(['-ns:0', '-links:User:Lihaohong/Sandbox3'])
gen = gen.getCombinedGenerator()
result = dict()
for p in gen:
    first = list(p.revisions(reverse=True, total=1))[0]
    u = first['user']
    result[u] = result.get(u, 0) + 1
    print(u)
for user in sorted(result, key=lambda k: result[k], reverse=True):
    print(user, result[user])
