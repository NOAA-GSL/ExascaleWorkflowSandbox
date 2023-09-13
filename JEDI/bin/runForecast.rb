#!/usr/bin/ruby

# Get the base directory
baseDir=File.expand_path('../..',__FILE__)

# Add bin directory to require search path
$LOAD_PATH.unshift "#{baseDir}/bin"

# Load libs
require 'yaml'
require 'date'
require 'fileutils'
require 'leadTime.rb'

# Load the experiment config
expConfig = YAML.load_file(ARGV[0])

# Get the analysis time
anlTime=ARGV[1]

# Load the base forecast config template
fcstConfig = YAML.load_file("#{baseDir}/yaml/forecast.yaml")

# Run forecasts with and without assimilation
["on", "off"].each do |assimilationOnOff|

  # Create forecast output directory
  expDir = "#{baseDir}/experiments/#{expConfig['Experiment']['Name']}"
  fcstDir = "#{expDir}/forecasts/#{anlTime}/assimilation_#{assimilationOnOff}"
  FileUtils.mkdir_p("#{fcstDir}")

  anlFile = "test.an.#{anlTime}"
  if expConfig['Experiment']['Begin'] == anlTime
    # If this is the first cycle, go get the analysis from input_data
    FileUtils.cp("#{baseDir}/input_data/#{anlFile}.l95", "#{fcstDir}/#{anlFile}")
  elsif assimilationOnOff=="off"
    # Otherwise, if assimilation is off go get the analysis from previous cycle assimilation on forecast
    prevCycle = (DateTime.parse(anlTime).to_time - LeadTime.fcstToSeconds(expConfig['Experiment']['Cycle Frequency'])).strftime("%Y-%m-%dT%H:%M:%SZ")
    bkgFile = "test.fc.#{prevCycle}.#{expConfig['Experiment']['Cycle Frequency']}"
    FileUtils.cp("#{expDir}/forecasts/#{prevCycle}/assimilation_on/#{bkgFile}", "#{fcstDir}/#{anlFile}")
  end

  # Set forecast configuration initial conditions
  fcstConfig["initial"]["filename"] = "#{fcstDir}/#{anlFile}"
  fcstConfig["initial"]["date"] = anlTime

  # Set the forecast length configuration
  fcstConfig["forecast_length"] = expConfig['Forecast']['Length']

  # Set configuration for forecast data output
  fcstConfig["output"]["datadir"] = "#{fcstDir}"
  fcstConfig["output"]["date"] = anlTime
  fcstConfig["output"]["frequency"] = expConfig['Forecast']['Frequency']

  # Write out updated truth config
  FileUtils.mkdir_p("#{expDir}/yaml")
  File.open("#{expDir}/yaml/forecast.#{anlTime}.yaml", "w") { |f| YAML.dump(fcstConfig, f) }

  # Save the experiment config
  File.open("#{expDir}/yaml/#{expConfig['Experiment']['Name']}.yaml", "w") { |f| YAML.dump(expConfig, f) }

  # Run the truth forecast
  system("#{expConfig['JEDI Path']}/bin/l95_forecast.x #{expDir}/yaml/forecast.#{anlTime}.yaml > #{fcstDir}/runForecast.stdout")

  if $?.exitstatus != 0
    raise "runForecast failed!  See #{fcstDir}/runForecast.stdout"
  end

end
