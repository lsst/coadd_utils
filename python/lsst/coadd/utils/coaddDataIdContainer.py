import lsst.pipe.base as pipeBase

__all__=["CoaddDataIdContainer"]

class CoaddDataIdContainer(pipeBase.DataIdContainer):
    """A version of lsst.pipe.base.DataIdContainer specialized for coaddition.

    Required because butler.subset does not support patch and tract

    This code was originally in pipe_tasks (coaddBase.py)
    """
    def getSkymap(self, namespace, datasetType):
        """Only retrieve skymap if required"""
        if not hasattr(self, "_skymap"):
            self._skymap = namespace.butler.get(datasetType + "_skyMap")
        return self._skymap

    def makeDataRefList(self, namespace):
        """Make self.refList from self.idList
        """
        datasetType = namespace.config.coaddName + "Coadd"
        validKeys = namespace.butler.getKeys(datasetType=datasetType, level=self.level)

        for dataId in self.idList:
            for key in validKeys:
                if key in ("tract", "patch"):
                    # Will deal with these explicitly
                    continue
                if key not in dataId:
                    raise argparse.ArgumentError(None, "--id must include " + key)

            # tract and patch are required; iterate over them if not provided
            if not "tract" in dataId:
                if "patch" in dataId:
                    raise RuntimeError("'patch' cannot be specified without 'tract'")
                addList = [dict(tract=tract.getId(), patch="%d,%d" % patch.getIndex(), **dataId)
                           for tract in self.getSkymap(namespace, datasetType) for patch in tract]
            elif not "patch" in dataId:
                tract = self.getSkymap(namespace, datasetType)[dataId["tract"]]
                import pdb
                pdb.set_trace()
                addList = [dict(patch="%d,%d" % patch.getIndex(), **dataId) for patch in tract]
            else:
                addList = [dataId]

            self.refList += [namespace.butler.dataRef(datasetType=datasetType, dataId=addId)
                             for addId in addList]

