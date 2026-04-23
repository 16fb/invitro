/*
 * MIT License
 *
 * Copyright (c) 2023 EASL and the vHive community
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

package trace

import (
	"math"
	"testing"

	// Temp
	"encoding/json"
	"os"
	"strconv"

	"sort"

	log "github.com/sirupsen/logrus"
	"github.com/vhive-serverless/loader/pkg/common"
)

// TODO, separate into 2 functions for better testing.
func TestFunction(t *testing.T) {
	tracePath := "test_data/AzureFunctionsInvocationTraceForTwoWeeksJan2021.csv"
	durationToParse := 10
	yamlPath := "dummy"

	traceParser := NewAzure2021Parser(tracePath, durationToParse, yamlPath)
	functions := traceParser.Parse()

	ReadOrWriteSpecificationToFile(functions, true, false)

	durationToParse = 21
}

// Test read data and deriving "start_timestamp" into InvocationTracker hashmap
func TestParseCSVFile(t *testing.T) {
	var filePath string = "test_data/Azure2021.csv"
	invocationTracker := ParseCSVFile(filePath)

	if len(invocationTracker) == 0 {
		t.Fatal("No keys defined in resultant invocation tracker.")
	}

	if len(invocationTracker) != 14 {
		t.Fatal("Unexpected number of keys in invocation tracker.")
	}

	/* Test first data row */
	appHash := "aaaaa2c01926d19690e5ec308bab64ef97950b75b1c7582283e0783fce1751d8"
	funcHash := "11111f8758c8c2a20082c161e955405e950439f0503522fe129e709a5dc0e58f"
	uniqueFunctionID := UniqueFunctionID{appHash, funcHash}

	invocationSlice, exists := invocationTracker[uniqueFunctionID]
	if !exists {
		t.Fatal("Example functionID does not exist.")
	}

	if invocationSlice[0].startTime != 1.00000 ||
		invocationSlice[0].duration != 9.000 {
		t.Errorf("Unexpected 'startTime' or 'duration' values. Got %f %f, expected 1.0 and 9.0",
			invocationSlice[0].startTime, invocationSlice[0].duration)
	}

	/* Test function with multiple invocations */
	appHash2 := "bbbbb2c01926d19690e5ec308bab64ef97950b75b1c7582283e0783fce1751d8"
	funcHash2 := "11111f8758c8c2a20082c161e955405e950439f0503522fe129e709a5dc0e58f"
	uniqueFunctionID2 := UniqueFunctionID{appHash2, funcHash2}

	invocationSlice2, exists2 := invocationTracker[uniqueFunctionID2]
	if !exists2 {
		t.Fatal("Multi-invocation function does not exist.")
	}
	if len(invocationSlice2) == 0 {
		t.Fatal("Multi-invocation function is empty.")
	}
	if len(invocationSlice2) != 16 {
		t.Fatal("Multi-invocation function has incorrect number of invocations.")
	}

	sort.Slice(invocationSlice2, func(i, j int) bool {
		return invocationSlice2[i].startTime < invocationSlice2[j].startTime
	})

	expectedTimestamp := [...]float64{122.0, 122.1, 122.2, 122.3, 122.4, 122.5, 122.6, 122.7, 122.8, 122.9, 123.0, 123.1, 123.2, 123.3, 123.4, 123.5}
	expectedDuration := 9.0
	tolerance := 0.00001
	for i, invocation := range invocationSlice2 {
		if math.Abs(invocation.startTime-expectedTimestamp[i]) > tolerance {
			t.Errorf("Incorrect startTime. Expected %f got %f", expectedTimestamp[i], invocation.startTime)
		}
		if math.Abs(invocation.duration-expectedDuration) > tolerance {
			t.Errorf("Incorrect duration. Expected 9.0 got %f", invocation.duration)
		}
	}
}

func ReadOrWriteSpecificationToFile(functions []*common.Function, writeIATsToFile bool, readIATsFromFile bool) {
	if writeIATsToFile && readIATsFromFile {
		log.Fatal("Invalid loader configuration. No point to read and write IATs within the same run.")
	}

	if readIATsFromFile {
		// Parse and read IATs Function Specifications
		for i := range functions {
			var spec common.FunctionSpecification

			iatFile, _ := os.ReadFile("iat" + strconv.Itoa(i) + ".json")
			err := json.Unmarshal(iatFile, &spec)
			if err != nil {
				log.Fatalf("Failed to unmarshal IAT file: %s", err)
			}
			functions[i].Specification = &spec
		}

		log.Info("IATs have been read from file(s).")
	}

	if writeIATsToFile {
		// Writes IATs Function Specifictions to .jsons file
		for i, function := range functions {
			file, _ := json.MarshalIndent(function.Specification, "", " ")
			err := os.WriteFile("iat"+strconv.Itoa(i)+".json", file, 0644)
			if err != nil {
				log.Fatalf("Writing the loader config file failed: %s", err)
			}
		}

		log.Info("IATs have been generated.. The program has exited.")
		os.Exit(0)
	}
}
