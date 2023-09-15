#!/usr/bin/ruby

# Get the base directory
baseDir=File.expand_path('../..',__FILE__)

# Add bin directory to require search path
$LOAD_PATH.unshift "#{baseDir}/bin"

# Load libs
require 'date'
require 'yaml'
require 'fileutils'
require 'leadTime.rb'

# Load the experiment config
expConfig = YAML.load_file(ARGV[0])

# Get the experiment forecast time range parameters
expStart = DateTime.parse(expConfig['Experiment']['Begin']).to_time
expFreq = LeadTime.fcstToSeconds(expConfig['Experiment']['Cycle Frequency'])
expEnd = expStart + LeadTime.fcstToSeconds(expConfig['Experiment']['Length']) - expFreq

# Get the verification spinup
spinup = LeadTime.fcstToSeconds(expConfig['Verification']['Spinup'])

# Get the experiment directory
expDir = "#{baseDir}/experiments/#{expConfig['Experiment']['Name']}"

# Create the verification directory
FileUtils.mkdir_p("#{expDir}/verify")

# Calculate mean MSE/RMSE for each forecast lead time
mses = { "on" => {}, "off" => {} }
f=0
while f <= LeadTime.fcstToSeconds(expConfig['Forecast']['Length'])

  mses["on"][f] = []
  mses["off"][f] = []

  # Verify this forecast lead time, f, for each cycle, t
  t = expStart + spinup
  while t <= expEnd

    # Calculate the valid time for this cycle and lead time
    validTime = t + f

    # Find truth forecast lead time corresponding to the valid time
    validTruthFcst = LeadTime.secondsToFcst(validTime - expStart)

    # Construct the truth filename
    truthFilename = "#{expDir}/truth/truth.fc.#{expConfig['Experiment']['Begin']}.#{validTruthFcst}"
    truth = IO.readlines(truthFilename,"\n")[2].split

    ["on", "off"].each do |assimilationOnOff|

      # Get the forecast directory
      fcstDir = "#{expDir}/forecasts/#{t.strftime("%Y-%m-%dT%H:%M:%SZ")}/assimilation_#{assimilationOnOff}"

      # Construct the forecast filename
      fcstFilename = "#{fcstDir}/test.fc.#{t.strftime("%Y-%m-%dT%H:%M:%SZ")}.#{LeadTime.secondsToFcst(f)}"
      fcst = IO.readlines(fcstFilename,"\n")[2].split

      # Calculate the MSE
      mse, i, size = 0.0, 0, truth.size
      while i < size
        mse += (fcst[i].to_f - truth[i].to_f) * (fcst[i].to_f - truth[i].to_f)
        i += 1
      end
      mses[assimilationOnOff][f] << mse / size

    end

    t = t + expFreq

  end

  f = f + LeadTime.fcstToSeconds(expConfig['Forecast']['Frequency'])

end

# Write out verification stats
File.open("#{expDir}/verify/verify.dat", "w") do |verifyFile|

  # Write column headers
  verifyFile.puts "LeadTime AssimilationOn AssimilationOff"

  f=0
  while f <= LeadTime.fcstToSeconds(expConfig['Forecast']['Length'])

    mseOn, mseOff, i, size = 0.0, 0.0, 0, mses["on"][f].size
    while i < size
      mseOn += mses["on"][f][i]
      mseOff += mses["off"][f][i]
      i += 1
    end

    verifyFile.puts "#{LeadTime.secondsToFcst(f)} #{mseOn/size} #{mseOff/size}"

    f = f + LeadTime.fcstToSeconds(expConfig['Forecast']['Frequency'])

  end

end

# Produce a plot
plgCmd = "gnuplot -e " + '"' + "baseDir='#{baseDir}'; expName='#{expConfig['Experiment']['Name']}'" + '"' + " #{baseDir}/bin/plotVerify.plg"
system(plgCmd)
