#!/usr/bin/ruby

# Get the base directory
baseDir=File.expand_path('../..',__FILE__)

# Add bin directory to require search path
$LOAD_PATH.unshift "#{baseDir}/bin"

# Load libs
require 'yaml'
require 'fileutils'
require 'date'
require 'leadTime.rb'

# Load the experiment config
expConfig = YAML.load_file(ARGV[0])

# Get the assimilation type (3d, 4d)
assimilationType = expConfig['Assimilation']['Type']

# Load the base obs config template
obsConfig = YAML.load_file("#{baseDir}/yaml/makeobs.#{assimilationType}.yaml")

# Create experiment obs output directory
expDir = "#{baseDir}/experiments/#{expConfig['Experiment']['Name']}"
FileUtils.rm_rf("#{expDir}/obs")
FileUtils.mkdir_p("#{expDir}/obs")

# Get the experiment forecast time range parameters
expStart=DateTime.parse(expConfig['Experiment']['Begin']).to_time
expFreq=LeadTime.fcstToSeconds(expConfig['Experiment']['Cycle Frequency'])
expEnd=expStart + LeadTime.fcstToSeconds(expConfig['Experiment']['Length']) - expFreq

# Create obs for each analysis time in the experiment
t=expStart + expFreq
while t <= expEnd

  puts "Making obs for cycle: #{t.inspect}"
 
  # Setup obs output file configuration
  obsConfig["Observations"]["ObsTypes"].each_with_index do |ob, i|
    obsConfig["Observations"]["ObsTypes"][i]["ObsData"]["ObsDataOut"]["filename"] = "#{expDir}/obs/l95.truth.#{assimilationType}.#{t.strftime("%Y-%m-%dT%H:%M:%SZ")}.obt"
  end

  # Setup obs generation window

  # Setup assimilation window configuration
  assimStart = (t + LeadTime.fcstToSeconds(expConfig['Assimilation']['Window Begin']))
  assimEnd = assimStart + LeadTime.fcstToSeconds(expConfig['Assimilation']['Window Length'])
  obsConfig["Assimilation Window"]["Begin"] = assimStart.strftime("%Y-%m-%dT%H:%M:%SZ")
  obsConfig["Assimilation Window"]["End"] = assimEnd.strftime("%Y-%m-%dT%H:%M:%SZ")

  # Setup the obs initial conditions
  truthInit = LeadTime.secondsToFcst((assimStart - DateTime.parse(expConfig['Experiment']['Begin']).to_time).to_i)
  obsConfig["Initial Condition"]["filename"] = "#{expDir}/truth/truth.fc.#{expConfig['Experiment']['Begin']}.#{truthInit}"
  obsConfig["Initial Condition"]["date"] = obsConfig["Assimilation Window"]["Begin"]

  # Handle obs filters, if any
  if (obsConfig["Observations"]["ObsFilters"])
    obsConfig["Observations"]["ObsFilters"].each_with_index do |ob, i|
      obsConfig["Observations"]["ObsFilters"][i]["filename"] = "#{expDir}/obs/l95.#{assimilationType}.#{t.strftime("%Y-%m-%dT%H:%M:%SZ")}.gom"
    end
  end

  # Write out updated makeobs config
  FileUtils.mkdir_p("#{expDir}/yaml")
  File.open("#{expDir}/yaml/makeobs.#{assimilationType}.#{t.strftime("%Y-%m-%dT%H:%M:%SZ")}.yaml", "w") { |f| YAML.dump(obsConfig, f) }

  # Save the experiment config
  File.open("#{expDir}/yaml/#{expConfig['Experiment']['Name']}.yaml", "w") { |f| YAML.dump(expConfig, f) }

  # Run the truth forecast
  system("#{expConfig['JEDI Path']}/bin/l95_makeobs.x #{expDir}/yaml/makeobs.#{assimilationType}.#{t.strftime("%Y-%m-%dT%H:%M:%SZ")}.yaml >> #{expDir}/obs/makeObs.stdout")

  if $?.exitstatus != 0
    raise "makeObs failed!  See #{expDir}/obs/makeObs.stdout"
  end

  t = t + expFreq

end
