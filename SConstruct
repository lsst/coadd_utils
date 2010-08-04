# -*- python -*-
#
# Setup our environment
#
import glob
import os.path
import lsst.SConsUtils as scons

try:
    scons.ConfigureDependentProducts
except AttributeError:
    import lsst.afw.SconsUtils
    scons.ConfigureDependentProducts = lsst.afw.SconsUtils.ConfigureDependentProducts

env = scons.makeEnv("coadd_utils",
                    r"$HeadURL$",
                    scons.ConfigureDependentProducts("coadd_utils"))

env.libs["coadd_utils"] += env.getlibs("boost wcslib cfitsio minuit2 gsl utils daf_base daf_data") + \
    env.getlibs("daf_persistence pex_exceptions pex_logging pex_policy security afw")

#
# Build/install things
#
for d in Split("doc examples lib python/lsst/coadd/utils tests"):
    SConscript(os.path.join(d, "SConscript"))

env['IgnoreFiles'] = r"(~$|\.pyc$|^\.svn$|\.o$)"

Alias("install", [
    env.InstallAs(os.path.join(env['prefix'], "doc", "doxygen"), os.path.join("doc", "htmlDir")),
    env.Install(env['prefix'], "examples"),
    env.Install(env['prefix'], "include"),
    env.Install(env['prefix'], "lib"),
    env.Install(env['prefix'], "python"),
    env.Install(env['prefix'], "src"),
    env.Install(env['prefix'], "tests"),
    env.InstallEups(env['prefix'] + "/ups"),
])

scons.CleanTree(r"*~ core *.so *.os *.o *.pyc")

files = scons.filesToTag()
if files:
    env.Command("TAGS", files, "etags -o $TARGET $SOURCES")

env.Declare()
env.Help("""
Utilities for coaddition of images
""")
