# %%
import click
import json
import sys
from pathlib import Path
import os
import numpy as np
import random


# %%
class CustomDataset:
    def __init__(self):
        self.DIR = Path(__file__).parent.resolve()

    def computeJsonAnswers(self, answersPath, metadataPath, outputname):
        with open(answersPath, "r") as f:
            answers = json.load(f)
        with open(
            outputname,
            "w",
        ) as answ:
            json.dump(answers, answ, ensure_ascii=False, indent=3)

    def computeInvertJsonAnswers(self, answersPath, metadataPath, outputname):
        with open(answersPath, "r") as f:
            answers = json.load(f)
        workerAnswers = {}
        for task in answers:
            for worker in answers[task]:
                workerAnswers[worker][task] = answers[task][worker]

        with open(
            outputname,
            "w",
        ) as answ:
            json.dump(answers, answ, ensure_ascii=False, indent=3)

    def computeRodriguezAnswers(self, answersPath, outputname):
        crowdlabels = np.loadtxt(answersPath)
        res_train = {task: {} for task in range(crowdlabels.shape[0])}
        for id_, task in enumerate(crowdlabels):
            where = np.where(task != -1)[0]
            for worker in where:
                res_train[id_][int(worker)] = int(task[worker])
        with open(
            outputname,
            "w",
        ) as answ:
            json.dump(res_train, answ, ensure_ascii=False, indent=3)

    # %%

    def writeSymlink(self, folder, file, currentPath, position):
        parent = file.parent.name
        currentFile = currentPath / folder / parent / f"{file.stem}-{position}.jpg"
        reversedParents = (currentFile.parents)[1::-1]

        for subfolder in reversedParents:
            os.makedirs(subfolder, exist_ok=True)
        if currentFile.exists():
            return
        os.symlink(
            file.absolute(),
            currentPath / folder / parent / f"{file.stem}-{position}.jpg",
        )

    # %%
    def setfolders(
        self,
        answers_format,
        answers,
        metadata,
        label_names,
        files_path,
        train_path,
        test_ground_truth,
        test_path,
        val_path,
    ):
        answersPath = Path(answers)

        if answers_format == 0:
            self.computeRodriguezAnswers(answersPath, "answers.json")
        elif answers_format == 1:
            if metadata == "":
                click.echo("Please provide a valid metadata file")
                sys.exit(1)
            else:
                metadataPath = Path(metadata)
                self.computeJsonAnswers(answersPath, metadataPath, "answers.json")
        elif answers_format == 2:
            if metadata == "":
                click.echo("Please provide a valid metadata file")
                sys.exit(1)
            else:
                metadataPath = Path(metadata)
                self.computeInvertJsonAnswers(answersPath, metadataPath, "answers.json")

        ##################################################################
        ## From now on, "./answers.json" is complete                    ##
        ##################################################################

        os.makedirs("train/", exist_ok=True)  # TODO : change to false
        os.makedirs("val/", exist_ok=True)  # TODO : change to false
        os.makedirs("test/", exist_ok=True)  # TODO : change to false

        with open("./answers.json", "r") as f:
            answersJson = json.load(f)

        filenameTrainPath = Path(files_path)
        orig_name = np.loadtxt(filenameTrainPath, dtype=str)
        labelNamesPath = Path(label_names)
        print(labelNamesPath)
        label_namesTab = np.loadtxt(labelNamesPath, dtype=str)

        if val_path == "":
            click.echo(
                "No val path provided, samples from the train set will be used instead"
            )

        currentPath = Path(".")
        trainPath = Path(train_path)
        testPath = Path(test_path)

        i = orig_name.shape[0]
        for j, file in enumerate(testPath.glob("*/*")):
            self.writeSymlink("test", file, currentPath, i)
            i += 1

        random.seed(0)
        for j, file in enumerate(trainPath.glob("*/*")):
            rand_num = random.uniform(0, 100)
            if rand_num < 20:
                self.writeSymlink(
                    "val", file, currentPath, np.where(orig_name == file.name)[0][0]
                )
            else:
                self.writeSymlink(
                    "train", file, currentPath, np.where(orig_name == file.name)[0][0]
                )

        if test_ground_truth == "":
            testPath = Path("./test/")
            res_test = {task: {} for task in range(orig_name.shape[0], i)}
            for j, file in enumerate(testPath.glob("*/*")):
                parent = file.parent.name
                parentId = np.where(label_namesTab == parent)[0][0]
                taskId = file.stem.split("-")[-1]
                res_test[int(taskId)][0] = int(parentId)
            with open(
                "./test_groundTruth.json",
                "w",
            ) as answ:
                json.dump(res_test, answ, ensure_ascii=False, indent=3)
        else:
            if answers_format == 0:
                self.computeRodriguezAnswers(answersPath, "test_groundTruth.json")
            elif answers_format == 1:
                if metadata == "":
                    click.echo("Please provide a valid metadata file")
                    sys.exit(1)
                else:
                    metadataPath = Path(metadata)
                    self.computeJsonAnswers(answersPath, metadataPath)
            elif answers_format == 2:
                if metadata == "":
                    click.echo("Please provide a valid metadata file")
                    sys.exit(1)
                else:
                    metadataPath = Path(metadata)
                    self.computeJsonAnswers(answersPath, metadataPath)
            print("TODO : Test ground truth provided")

    # %%